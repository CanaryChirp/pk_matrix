from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

import collections

class GameSettingsForm(forms.Form):
    CHOICES1 = (('1', 'Show card images (fast connection)',), ('2', 'Show card text (slow connection)',))
    show_images = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES1, initial='1')
    CHOICES2 = (('1', 'Show opponent cards',), ('2', 'Hide opponent cards',))
    opponent_cards = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES2, initial='1')
    CHOICES3 = (('1', 'Show training text',), ('2', 'Hide training text',))
    training_text = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES3, initial='1')

    # 2 - 15, integer only
    number_of_players = forms.IntegerField(validators=[MinValueValidator(2), MaxValueValidator(15)], initial=4, help_text='Enter an integer, 2 - 15')
    # 10 - 5000, integer only
    starting_stacks = forms.IntegerField(validators=[MinValueValidator(10), MaxValueValidator(5000)], initial=200, help_text='Enter an integer, 10 - 5000')

    # contact_name = forms.CharField(required=True)
    # contact_email = forms.EmailField(required=True)
    # content = forms.CharField(
    #    required=True,
#        widget=forms.Textarea
#        )

def profile_choices(profile_set):
    choices_list = []
    idx = 1
    for prof in profile_set.ai_profile_set.all():
        choices_list.append((str(prof.id), "Profile {}".format(prof.id)))
        idx += 1
    return choices_list
    """
    CHOICES = (
        ('1', 'Option 1'),
        ('2', 'Option 2'),
        ('3', 'Option 3'),
    )
    return CHOICES
    """


class AISettingsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.profile_set = kwargs.pop('profile_set')
        super(AISettingsForm, self).__init__(*args, **kwargs)
        self.fields['Profile to edit:'] = forms.ChoiceField(
            choices=profile_choices(self.profile_set),
            widget=forms.Select(attrs={"onchange":'this.form.submit()'}) )
        fields_key_order = ["Profile to edit:", "percentage", "aggression",
            "intelligence", "randomness", "adaptability"]
        self.fields = collections.OrderedDict((k, self.fields[k]) for k in fields_key_order)

    percentage = forms.IntegerField(validators=[MinValueValidator(0),
        MaxValueValidator(100)], initial=100, help_text=
        """Enter an integer, 0 - 100, for percentage of opponents.  Other
        profiles will be normalized accordingly.""")

    aggression = forms.IntegerField(validators=[MinValueValidator(0),
        MaxValueValidator(100)], initial=20, help_text=
        """Enter an integer, 0 - 100.""")

    intelligence = forms.IntegerField(validators=[MinValueValidator(0),
        MaxValueValidator(100)], initial=50, help_text=
        """Enter an integer, 0 - 100.""")

    randomness = forms.IntegerField(validators=[MinValueValidator(0),
        MaxValueValidator(100)], initial=20, help_text=
        """Enter an integer, 0 - 100.""")

    adaptability = forms.IntegerField(validators=[MinValueValidator(0),
        MaxValueValidator(100)], initial=0, help_text=
        """Enter an integer, 0 - 100.""")

    def refresh(self, *args, **kwargs):
        self.profile_set = kwargs.pop('profile_set')
        self.fields['Profile to edit:'] = forms.ChoiceField(
            choices=profile_choices(self.profile_set) )




class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label='Select a file, then click \'upload\'',
        help_text=''
    )