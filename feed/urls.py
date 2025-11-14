from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^hot$", views.hot_feed, name="hot_feed"),
    url(r"^posts/$", views.post_create, name="post_create"),
    url(r"^posts/(?P<post_id>[0-9]+)/$", views.post_detail, name="post_detail"),
    url(r"^posts/(?P<post_id>[0-9]+)/update/$", views.post_update, name="post_update"),
    url(r"^posts/(?P<post_id>[0-9]+)/delete/$", views.post_delete, name="post_delete"),
    url(
        r"^posts/(?P<post_id>[0-9]+)/aggregates/$",
        views.post_aggregates,
        name="post_aggregates",
    ),
    url(
        r"^posts/(?P<post_id>[0-9]+)/likes/$", views.like_create, name="like_create"
    ),
    url(
        r"^posts/(?P<post_id>[0-9]+)/likes/(?P<user_id>[0-9]+)/$",
        views.like_delete,
        name="like_delete",
    ),
    url(
        r"^posts/(?P<post_id>[0-9]+)/likes/(?P<user_id>[0-9]+)/status/$",
        views.like_status,
        name="like_status",
    ),
]
