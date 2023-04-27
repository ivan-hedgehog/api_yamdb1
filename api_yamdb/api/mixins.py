from rest_framework import filters, mixins, viewsets

from .permissions import IsSuperuserOrAdminPermission, ReadOnlyPermission


class CreateListDestroyViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    permission_classes = (ReadOnlyPermission | IsSuperuserOrAdminPermission,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'
