from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, TeamViewSet, magic_link_download, magic_link_info

router = DefaultRouter()
router.register(r'files', FileViewSet, basename='file')
router.register(r'teams', TeamViewSet, basename='team')

urlpatterns = [
    path('', include(router.urls)),
    path('share/<str:token>/download/', magic_link_download, name='magic-download'),
    path('share/<str:token>/info/', magic_link_info, name='magic-info'),
]
