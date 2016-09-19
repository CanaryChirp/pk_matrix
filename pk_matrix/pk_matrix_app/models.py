from django.db import models
from django.contrib.sessions.backends.db import SessionStore
from datetime import datetime

import random, re

NAMES = ["John", "Fred", "Susie", "Brian", "Steve", "Shirley", "Jessica",
         "Alfred", "Frank", "Kate", "Jim", "Lisa", "Jose", "Manuel"]
DECK_FULL = ["Ah", "2h", "3h", "4h", "5h", "6h", "7h", "8h", "9h", "10h", "Jh", "Qh",
             "Kh", "As", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s", "10s", "Js",
             "Qs", "Ks", "Ac", "2c", "3c", "4c", "5c", "6c", "7c", "8c", "9c", "10c",
             "Jc", "Qc", "Kc", "Ad", "2d", "3d", "4d", "5d", "6d", "7d", "8d", "9d",
             "10d", "Jd", "Qd", "Kd"]
BIG_BLIND = 10
ACTIONS = ["Fold", "Call", "Raise"]
LOG = "logfile.txt"

class Game(models.Model):

	"""
	Handles game status information and session key
	"""

	n = models.IntegerField(default=4)
	stack_start = models.IntegerField(default=200)
	game_over = models.BooleanField(default=False)
	pot = models.IntegerField(default=0)
	# game status key:
	#   in progress: "",
	#   wait for input: "waiting",
	#   go to showdown: "showdown",
	#   round over (all but one folded): "done"
	#   tourney over: "end"
	myStatus = models.CharField(max_length=255, default="")
	user_input = models.CharField(max_length=255, default="")
	current_round = models.CharField(max_length=255, default="")
	winner = models.CharField(max_length=255, default="")
	training_text = models.CharField(max_length=255, default="")
	# add this for authenticated users
	#   maker = models.ForeignKey(AnonymousUser, null=True, blank=True)
	# use this for anonymous users (saves session data only)
	session_key = models.CharField(max_length=255, default="", null=True, blank=True)

	def printlog(self, text):
		"""
		print to logfile stored in LOG
		"""
		f = open(LOG, 'a')
		f.write(text)
		f.write("\n")
		f.close()

	def name_players(self):
		"""
		assign opponent names randomly from NAMES
		assign hero random position
		allocate stacks from stack_start
		"""
		self.printlog("\n")
		self.printlog("in models.game.name_players")

		used = []
		your_posn = random.randint(0, self.n-1)
		for idx in range(self.n):
			if idx == your_posn:
				pass
				player = Hero(name="You", order=idx, game=self)
			else:
				name = random.choice(NAMES)
				while name in used:
					name = random.choice(NAMES)
				player = Player(name=name, order=idx, game=self)
				used.append(name)
			player.stack = self.stack_start
			player.save()
			self.printlog(player.name)
			self.printlog("order is: {}".format(player.order))

	def title_players(self):
		"""
		give all players titles according to position
		special case for heads-up play (only 2 players)
		"""
		self.printlog("\n")
		self.printlog("in models.game.title_players")

		for player in self.player_set.all():
			if self.player_set.all().count() == 2:
				self.printlog("only 2 players")
				if player.order == 0:
					player.title = "Big Blind"
				elif player.order == 1:
					player.title = "Dealer, Small Blind"
				else:
					player.title = ""
				if player.order == (Player.objects.count() - 1):
					player.title += "Dealer"
			else:
				self.printlog("more than 2 players")
				if player.order == 0:
					player.title = "Small Blind"
				elif player.order == 1:
					player.title = "Big Blind"
				else:
					player.title = ""
				if player.order == (Player.objects.count() - 1):
					player.title = "Dealer"
			player.save()
			self.printlog(player.name)
			self.printlog("title is: {}".format(player.title))
			self.printlog("order is: {}".format(player.order))


	def clean_players(self):
		"""
		remove data from previous hand
		"""
		self.printlog("\n")
		self.printlog("in models.game.clean_players")

		for player in self.player_set.all():
			player.last_act = ""
			player.money_in = 0
			player.rank = 0
			player.best_hand = ""
			player.save()

	def prepare_game(self):
		"""
		store session key, retrieve game settings from session dict
		if new game, name players
		otherwise clean and rotate
		remove existing cards, deal hole, set round
		"""
		self.printlog("\n")
		self.printlog("in models.game.prepare_game")

		session = SessionStore(session_key=self.session_key)
		self.n = session['n_players']
		self.stack_start = session['starting_stacks']
		self.save()
		self.table = Table()
		if self.player_set.count() == 0:
			self.name_players()
			self.myStatus == ""
			self.save()
		else:
			self.clean_players()
			self.rotate_players()
		for player in self.player_set.all():
			player.cards.all().delete()
		self.title_players()
		self.table.deal_hole(self)
		self.current_round = "pre_flop"
		self.printlog("setting current_round to {}".format(self.current_round))
		self.save()
		self.bet_set.all().delete()
		Bet(game=self).save()


	def start_pre_flop(self):
		"""
		start new betting round
		no return value, view will check game.myStatus
		"""
		self.printlog("\n")
		self.printlog("in models.game.start_pre_flop")
		bet = self.bet_set.first()
		bet.do_bet()
		self.refresh_from_db()

	def rotate_players(self):
		"""
		rotate players for next hand
		"""
		self.printlog("\n")
		self.printlog("in models.game.rotate_players")
		count = -1
		for player in self.player_set.all():
			if count < 0:
				player.order = self.player_set.count() - 1
			else:
				player.order = count
			count += 1
			player.save()
			self.printlog(player.name)
			self.printlog("order is: {}".format(player.order))

	def get_training_text(self):
		self.training_text = "cc training text here"

	def prepare_flop(self):
		"""
		prepare players for next round of betting
		set new round
		deal flop
		"""
		self.printlog("\n")
		self.printlog("in models.game.prepare_flop")

		for player in self.player_set.all():
			player.money_in = 0
			if player.last_act != "Fold":
				player.last_act = ""
			player.save()
		self.current_round = "flop"
		self.printlog("setting current_round to {}".format(self.current_round))
		self.table = Table()
		self.table.deal_flop(self)
		self.get_training_text()
		self.save()
		self.bet_set.all().delete()
		bet = Bet(game=self)
		bet.save()

	def flop(self):
		"""
		start new betting round
		no return value, view will check game.myStatus
		"""
		self.printlog("\n")
		self.printlog("in models.game.flop")
		bet = self.bet_set.first()
		bet.do_bet()

	def prepare_turn(self):
		"""
		prepare players for next round of betting
		set new round
		deal turn
		"""
		self.printlog("\n")
		self.printlog("in models.game.prepare_turn")

		for player in self.player_set.all():
			player.money_in = 0
			if player.last_act != "Fold":
				player.last_act = ""
			player.save()
		self.current_round = "turn"
		self.printlog("setting current_round to {}".format(self.current_round))
		self.table = Table()
		self.table.deal_turn(self)
		self.save()
		self.bet_set.all().delete()
		bet = Bet(game=self)
		bet.save()

	def turn(self):
		"""
		start new betting round
		no return value, view will check game.myStatus
		"""
		self.printlog("\n")
		self.printlog("in models.game.turn")
		bet = self.bet_set.first()
		bet.do_bet()

	def prepare_river(self):
		"""
		prepare players for next round of betting
		set new round
		deal river
		"""
		self.printlog("\n")
		self.printlog("in models.game.prepare_river")

		for player in self.player_set.all():
			player.money_in = 0
			if player.last_act != "Fold":
				player.last_act = ""
			player.save()
		self.current_round = "river"
		self.printlog("setting current_round to {}".format(self.current_round))
		self.table = Table()
		self.table.deal_river(self)
		self.save()
		self.bet_set.all().delete()
		bet = Bet(game=self)
		bet.save()

	def river(self):
		"""
		start new betting round
		no return value, view will check game.myStatus
		"""
		self.printlog("\n")
		self.printlog("in models.game.river")

		bet = self.bet_set.first()
		bet.do_bet()

	def showdown(self):
		"""
		deal any undealt cards
		find player whose best possible hand has the highest rank, set as winner
		"""
		self.printlog("\n")
		self.printlog("in models.game.showdown")

		# check if any rounds have not been dealt, if so, deal them
		p = self.player_set.first()
		table = Table()
		if p.cards.count() == 2:
			table.deal_flop(self)
		if p.cards.count() == 5:
			table.deal_turn(self)
		if p.cards.count() == 6:
			table.deal_river(self)
		# each player should now have 7 cards (incl. comm. cards)

		max_rank = 0
		for player in self.player_set.all():
			if player.last_act == 'Fold':
				continue
			self.printlog("\n")
			self.printlog(player.name)
			player.get_best_rank()
			if player.rank > max_rank:
				max_rank = player.rank
				max_name = player.name
		self.printlog("highest rank: {}".format(max_rank))
		self.printlog("winner: {}".format(max_name))
		self.winner = max_name
		self.save()

	def hand_over(self):
		"""
		award pot to winner
		delete any broke players
		end game if only one player left
		prepare players and game for next hand
		"""
		self.printlog("\n")
		self.printlog("in models.game.hand_over")

		for player in self.player_set.all():
			if player.name == self.winner:
				player.stack += self.pot
			if player.stack == 0:
				player.delete()
				continue
			player.money_in = 0
			player.last_act = ""
			player.save()
		self.pot = 0
		self.myStatus = ""
		if self.player_set.count() < 2:
			self.myStatus = "end"
		self.user_input = ""
		self.current_round = ""
		self.printlog("setting current_round to {}".format(self.current_round))
		self.winner = ""
		self.save()


class Card(models.Model):
	"""
	store data for one card
	many-to-many relationship with Player
	"""
	name = models.CharField(max_length=255)
	is_comm_card = models.BooleanField(default=True)

	def __str__(self):
		return self.name

class Player(models.Model):
	"""
	store data for player
	many-to-many relationship with Card
	"""
	name = models.CharField(max_length=255)
	order = models.IntegerField(default=0)
	title = models.CharField(max_length=255)
	money_in = models.IntegerField(default=0)
	last_act = models.CharField(max_length=255)
	stack = models.IntegerField(default=200)
	rank = models.IntegerField(default=0)
	best_hand = models.CharField(max_length=255)
	cards = models.ManyToManyField(Card)
	game = models.ForeignKey(Game)

	class Meta:
		ordering = ['order']

	def decide(self, call_amt, max_bid, do_blinds):

		if do_blinds and "Big Blind" in self.title:
			bet = BIG_BLIND
		elif do_blinds and "Small Blind" in self.title:
			bet = BIG_BLIND/2
		else:
			bet = self.get_bet(call_amt)
		self.game.printlog("{} chooses to {}".format(self.name, self.last_act))
		if self.game.myStatus == "waiting":
			return 0
		elif self.game.myStatus == "":

			if (max_bid and ((self.money_in + bet) > max_bid)):
				bet = max_bid - self.money_in
			if (self.stack - bet > 0):
				self.stack -= bet
				self.money_in += bet
				self.save()
				return bet
			else:
				self.last_act = "All In"
				bet = self.stack
				self.stack = 0
				self.money_in += bet
				self.save()
				return bet

	def fix(self, user_input):
		if 'r' in user_input.lower():
			return "Raise"
		elif 'c' in user_input.lower():
			return "Call"
		else:
			return "Fold"

	def get_bet(self, call_amt):

		action = ""
		if self.name == "You":
			if self.game.myStatus == "":
				self.game.myStatus = "waiting"
				self.game.save()
				return 0
			elif self.game.myStatus == "waiting":
				self.game.myStatus = ""
				self.game.save()
				action = self.fix(self.game.user_input)
				if action == "Raise":
				    try:
				        raise_mult = int(re.search(r'\d+', self.game.user_input).group(0))
				    except:
				        raise_mult = 2
				    if raise_mult < 1 or raise_mult > 10:
				        raise_mult = 2
		else:
			action = random.choice(ACTIONS)
			raise_mult = random.choice(range(2,5))
		self.last_act = action
		self.save()
		bet = 0
		if action == "Fold":
			bet = 0
		elif action == "Call":
			bet = call_amt - self.money_in
		elif action == "Raise":
			bet = call_amt - self.money_in + (BIG_BLIND / 2)*raise_mult
		return bet

	def __str__(self):
		return self.name

	def get_best_rank(self):
		cards = self.cards.all()
		br = Best_rank(cards)
		self.rank = br.best_rank
		self.best_hand = br.name
		self.save()

	def is_all_in(self):
		return self.last_act != "Fold" and self.stack == 0


class Hero(Player):

	def get_bet(self, call_amt):
		if self.game.myStatus == "":
			self.game.myStatus = "waiting"
			self.game.save()
			return 0
		elif self.game.myStatus == "waiting":
			self.game.myStatus = ""
			self.game.save()
			action = "Fold"
			self.last_act = action
			self.save()
			if action == "Fold":
				bet = 0
			elif action == "Call":
				bet = call_amt - self.money_in
			elif action == "Raise":
				bet = call_amt - self.money_in + (BIG_BLIND / 2)*random.choice(range(2,5))
			return bet

class Best_rank:
	def __init__(self, cards):
		self.cards = list(cards)
		self.get_best_rank()

	def get_best_rank(self):
		max_rank = 0
		max_hand = self.cards[:5]
		for idx in range(7):
			for jdx in range(idx + 1, 7):
				hand = self.cards[:]
				del hand[jdx]
				del hand[idx]
				ra = Rank(hand)
				rank = ra.rank
				if rank > max_rank:
					max_rank = rank
					max_hand = hand
					max_name = ra.name
		self.best_rank = max_rank
		self.best_hand = max_hand
		self.name = max_name

class Rank:
    def __init__(self, hand):
        self.hand = hand
        # troubleshooting
        self.rank = 0

        self.get_nums()
        self.get_suits()
        self.get_rank()

    def get_nums(self):
        self.nums = []
        for card in self.hand:
            if len(card.name) == 2:
                ch = card.name[0]
            else:
                self.nums.append(10)
                continue
            if ch == 'A':
                self.nums.append(14)
            elif ch == 'J':
                self.nums.append(11)
            elif ch == 'Q':
                self.nums.append(12)
            elif ch == 'K':
                self.nums.append(13)
            else:
                self.nums.append(int(ch))
        self.nums.sort()

    def get_suits(self):
        self.suits = []
        for card in self.hand:
            self.suits.append(card.name[-1])
        self.suits.sort()

    def get_rank(self):
        """retrieves value of hand in self.hand as a numeric value.
        each step up type ladder (e.g. high card -> pair -> 2 pair ...)
        increments the rank value by 100 points.  Points are then added
        for according to card value (with aces high) for high card, high
        pair, etc., as appropriate.

        :return: int
        """
        st = self.is_straight()
        fl = self.is_flush()
        rank_inc = 1000

        # ADD POINT INCREMENTS TO pair, trio, ...
        if st and fl:
            # Is a straight flush.
            # 8000 - 8999
            self.name = "Straight Flush"
            self.rank = rank_inc * 8 + self.get_high_card()
            return 0
        elif self.is_quad():
            # Is four of a kind.  ties are broken in checking method.
            # 7000 - 7999
            self.name = "Four of a Kind"
            self.rank += rank_inc * 7
            return 0
        elif self.is_full_house():
            # Is a full house.  ties are broken in checking method.
            # 6000 - 6999
            self.name = "Full House"
            self.rank += rank_inc * 6
            return 0
        elif fl:
            # Is a flush.
            # ranking not correct for flushes w/ matching high cards.  check those ties separately.
            # 5000 - 5999
            self.name = "Flush"
            self.rank = rank_inc * 5 + self.get_high_card()
            return 0
        elif st:
            # Is a straight.
            # 4000 - 4999
            self.name = "Straight"
            self.rank = rank_inc * 4 + self.get_high_card()
            return 0
        elif self.is_trio():
            # Is three of a kind. ties broken in checking method.
            # 3000 - 3999
            self.name = "Three of a Kind"
            self.rank += rank_inc * 3
            return 0
        elif self.is_two_pair():
            # Is two pair.  ties broken in checking method.
            # 2000 - 2999
            self.name = "Two Pair"
            self.rank += rank_inc * 2
            return 0
        elif self.is_pair():
            # Is a pair.  ties broken in checking method.
            # 1000 - 1999
            self.name = "Pair"
            self.rank += rank_inc
            return 0
        else:
            # garbage hand.  1 - 999
            self.name = "High Card"
            self.rank = self.get_high_card()
            return 0


    def get_high_card(self):
        if 1 in self.nums and "Straight" not in self.name:
            return 14
        else:
            return self.nums[-1]

    def is_two_pair(self):
        # four of a kind is excluded by if/elif in get_rank()
        count = 0
        idx = 0
        # troubleshooting
        idx_store = 0
        rank_storage = 0

        unpaired = 0
        while (idx < (len(self.nums) - 1)):
            if self.nums[idx] == self.nums[idx + 1]:
                if count == 1:
                    if idx_store == 1:
                        unpaired = self.nums[0]
                    elif idx == 3:
                        unpaired = self.nums[2]
                    else:
                        unpaired = self.nums[4]
                    self.rank = rank_storage*13 + self.nums[idx]*2*13 + unpaired
                    return True
                rank_storage = self.nums[idx]
                idx_store = idx
                count += 1
                idx += 2
            else:
                idx += 1
        return False

    def is_pair(self):
        for idx in range(len(self.nums) - 1):
            if self.nums[idx] == self.nums[idx + 1]:
                if idx == 3:
                    self.rank = self.nums[idx]*20 + self.nums[2]
                else:
                    self.rank = self.nums[idx]*20 + self.nums[-1]
                return True
        return False

    def is_trio(self):
        for idx in range(len(self.nums) - 2):
            if self.nums[idx] == self.nums[idx + 1] and self.nums[idx] == self.nums[idx + 2]:
                if idx == 2:
                    self.rank = self.nums[idx]*20 + self.nums[1]
                else:
                    self.rank = self.nums[idx]*20 + self.nums[4]
                return True
        return False

    def is_quad(self):
        for idx in range(len(self.nums) - 3):
            if self.nums[idx] == self.nums[idx + 1] and self.nums[idx] == self.nums[idx + 2] and self.nums[idx] == \
                    self.nums[idx + 3]:
                if idx == 0:
                    kicker_ind = 4
                else:
                    kicker_ind = 0
                self.rank = self.nums[idx]*20 + self.nums[kicker_ind]
                return True
        return False

    def is_straight(self):

        if self.is_straight_acelow():
            return True

        for idx in range(len(self.nums) - 1):
            if self.nums[idx] + 1 != self.nums[idx + 1]:
                return False
        return True

    def is_straight_acelow(self):

        nums_ah = self.nums[:]
        for idx in range(len(nums_ah)):
            if nums_ah[idx] == 14:
                nums_ah[idx] = 1
        nums_ah.sort()

        for idx in range(len(nums_ah) - 1):
            if nums_ah[idx] + 1 != nums_ah[idx + 1]:
                return False
        self.nums = nums_ah
        return True



    def is_flush(self):
        # TODO: figure out how to separate matching flushes better...
        for suit in self.suits:
            if suit != self.suits[0]:
                return False
        return True

    def is_full_house(self):
        end_check = (self.nums[0] == self.nums[1]) and (self.nums[-1] == self.nums[-2])
        trio_first = self.nums[2] == self.nums[0]
        trio_last = self.nums[2] == self.nums[-1]
        mid_check = trio_first or trio_last
        if end_check and mid_check:
            if trio_first:
                self.rank = 50*self.nums[0] + self.nums[4]
            else:
                self.rank = 50*self.nums[4] + self.nums[0]
            return True
        else:
            return False



class Table:
	def __init__(self):
		self.deck = DECK_FULL[:]

	def deal_hole(self, game):
		players = game.player_set.all()
		for player in players:
			player.cards.create(name=self.deal(), is_comm_card=False)
			player.cards.create(name=self.deal(), is_comm_card=False)

	def deal_flop(self, game):
		players = game.player_set.all()
		cards = []
		for idx in range(3):
			cards.append(self.deal())
		for player in players:
			for card in cards:
				player.cards.create(name=card, is_comm_card=True)

	def deal_turn(self, game):
		players = game.player_set.all()
		card = self.deal()
		for player in players:
			player.cards.create(name=card, is_comm_card=True)

	def deal_river(self, game):
		players = game.player_set.all()
		card = self.deal()
		for player in players:
			player.cards.create(name=card, is_comm_card=True)


	def deal(self):
		# TODO: get rid of check, b/c new deck for each hand
		try:
			card = random.choice(self.deck)
		except IndexError:
			self.new_deck()
			card = random.choice(self.deck)
		self.deck.remove(card)
		return card;

	def new_deck(self):
		self.deck = DECK_FULL[:]

class Bet(models.Model):

	max_in = models.IntegerField(default=0)
	do_blinds = models.BooleanField(default=True)
	call_amt = models.IntegerField(default=0)
	game = models.ForeignKey(Game)

	def allin_fix(self, m_in):
		for p in self.game.player_set.all():
			if p.money_in > m_in:
				p.stack += p.money_in - m_in
				p.money_in = m_in
				p.save()

	def do_bet(self):
		if self.call_amt == 0:
			self.call_amt = BIG_BLIND/2
		self.save()
		blinds_count = 0
		count = 0
		try:
			while True:
				for player in self.game.player_set.all():

					if self.game.myStatus == "waiting" and player.name != "You":
						continue

					count += 1
					if count > 10:
						return 0

					# skip player if they previously folded
					if player.last_act == "Fold":
						continue

					# get p's bet
					blinds_count += 1
					if blinds_count > 2:
						self.do_blinds = False
						self.save()
					self.refresh_from_db()
					newbet = player.decide(self.call_amt, self.max_in, self.do_blinds)
					self.game.pot += newbet
					self.game.save()
					if self.game.myStatus == "waiting":
						self.game.refresh_from_db()
						self.game.save()
						return 0
					elif self.game.myStatus == "":

						# make table adjustments if p is all-in
						if player.is_all_in():
							self.allin_fix(player.money_in)
							self.max_in = player.money_in

						# add p's bet to pot
						self.game.pot += newbet

						# increase call amount if necessary
						if player.money_in > self.call_amt or player.last_act == "All In":
							self.call_amt = player.money_in
							self.save()

						# count += 1
						if self.betting_done(self.call_amt):
							raise StopIteration

		except StopIteration:
			self.game.printlog("leaving betting")

	def betting_done(self, call_amt):
		# check if all but 1 have folded (True, set game.winner)
		# check if any is all_in (True, showdown)
		# check if all that haven't folded have met the call_amt (True)
		active_count = 0
		allin_count = 0
		no_action_count = 0
		less_than_call_count = 0

		for player in self.game.player_set.all():
			if player.last_act != "Fold":
				active_count += 1
				p_active = player
				if player.last_act == "All In":
					allin_count += 1
				if player.money_in < call_amt:
					less_than_call_count += 1
				if player.last_act == "":
					no_action_count += 1

		if active_count == 1:
			# all players but one have folded
			self.game.winner = p_active.name
			self.game.myStatus = "done"
			self.game.save()
			return True
		if less_than_call_count == 0 and no_action_count == 0:
			if allin_count > 0:
				# all players met call amt, at least one is all-in
				# self.showdown()
				# working here--send to showdown
				self.game.myStatus = "showdown"
				self.game.save()
				return True
			else:
				pass

			# all players met call amt, none are all-in
			# self.bet_cleanup()
			return True
		return False

class AI_Profile_Set(models.Model):
    session_key = models.CharField(max_length=255, default="", null=True, blank=True)

class AI_Profile(models.Model):
    percentage = models.IntegerField(default=100)
    aggression = models.IntegerField(default=0)
    intelligence = models.IntegerField(default=0)
    randomness = models.IntegerField(default=0)
    adaptability = models.IntegerField(default=0)
    profile_set = models.ForeignKey(AI_Profile_Set, null=True)


class Document(models.Model):
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')
    creation_date = models.DateTimeField(default=datetime.now, blank=True)