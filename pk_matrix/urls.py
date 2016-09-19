# from django.conf.urls.defaults import patterns, include, url
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
admin.autodiscover()

# from .pk_matrix_app import views

urlpatterns = patterns('',
    url(r'photo_test/$', 'pk_matrix.pk_matrix_app.views.list', name="list"),
    url(r'stats/$', 'pk_matrix.pk_matrix_app.views.stats', name="stats"),
    url(r'ai_settings/$', 'pk_matrix.pk_matrix_app.views.ai_settings', name="ai_settings"),
    url(r'settings/$', 'pk_matrix.pk_matrix_app.views.game_settings', name="game_settings"),
    url(r'settings/updated$', 'pk_matrix.pk_matrix_app.views.game_settings_updated', name="game_settings_updated"),
    url(r'new/$', 'pk_matrix.pk_matrix_app.views.new_game', name="new"),
    url(r'players/$', 'pk_matrix.pk_matrix_app.views.players', name="players"),
    url(r'tournament(?P<game_pk>\d+)/$', 'pk_matrix.pk_matrix_app.views.start_pre_flop', name="game_round"),
    url(r'tournament(?P<game_pk>\d+)/preflop$', 'pk_matrix.pk_matrix_app.views.continue_pre_flop', name="preflop"),
    url(r'tournament(?P<game_pk>\d+)/flop$', 'pk_matrix.pk_matrix_app.views.flop', name="flop"),
    url(r'tournament(?P<game_pk>\d+)/turn$', 'pk_matrix.pk_matrix_app.views.turn', name="turn"),
    url(r'tournament(?P<game_pk>\d+)/river$', 'pk_matrix.pk_matrix_app.views.river', name="river"),
    url(r'tournament(?P<game_pk>\d+)/showdown$', 'pk_matrix.pk_matrix_app.views.showdown', name="showdown"),
    url(r'^$', 'pk_matrix.pk_matrix_app.views.index', name='home'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)