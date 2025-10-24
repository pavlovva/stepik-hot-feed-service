from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^hot$", views.hot_feed, name="hot_feed"),
]
