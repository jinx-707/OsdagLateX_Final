from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes as perm
from rest_framework.response import Response
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from accounts.models import User
from .models import OsdagFile, FileAccess, FileAccessLog, Team, MagicLink
from .serializers import (
    OsdagFileSerializer, FileUploadSerializer, FileAccessSerializer,
    FileAccessLogSerializer, TeamSerializer, AddMemberSerializer
)
from .permissions import IsOwnerOrHasAccess, IsOwner, IsTeamCreatorOrMember


class FileViewSet(viewsets.ModelViewSet):
    queryset = OsdagFile.objects.all()
    serializer_class = OsdagFileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrHasAccess]

    def get_serializer_class(self):
        if self.action == 'create':
            return FileUploadSerializer
        return OsdagFileSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != request.user:
            FileAccessLog.objects.create(
                file=instance,
                user=request.user,
                action=FileAccessLog.Action.VIEW,
                details={'ip': request.META.get('REMOTE_ADDR', '')}
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwner])
    def share(self, request, pk=None):
        file_obj = self.get_object()
        email = request.data.get('email')
        team_id = request.data.get('team_id')
        permission_level = request.data.get('permission', 'view')
        expires_at = request.data.get('expires_at')

        if not email and not team_id:
            return Response(
                {'error': 'Either email or team_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_users = []
        if email:
            try:
                user = User.objects.get(email=email)
                if user == file_obj.owner:
                    return Response(
                        {'error': 'Cannot share with yourself'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                target_users.append(user)
            except User.DoesNotExist:
                return Response(
                    {'error': f'User with email {email} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        if team_id:
            try:
                team = Team.objects.get(id=team_id)
                if not team.members.filter(id=request.user.id).exists() and team.created_by != request.user:
                    return Response(
                        {'error': 'You are not a member of this team'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                target_users.extend(team.members.all())
            except Team.DoesNotExist:
                return Response(
                    {'error': 'Team not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        target_users = list(set(target_users) - {file_obj.owner})

        if not target_users:
            return Response(
                {'error': 'No valid users to share with'},
                status=status.HTTP_400_BAD_REQUEST
            )

        grants = []
        for user in target_users:
            grant, created = FileAccess.objects.update_or_create(
                file=file_obj,
                shared_with=user,
                defaults={
                    'permission': permission_level,
                    'expires_at': expires_at
                }
            )
            grants.append(grant)

        FileAccessLog.objects.create(
            file=file_obj,
            user=request.user,
            action=FileAccessLog.Action.SHARE,
            details={
                'shared_with': [u.email for u in target_users],
                'permission': permission_level
            }
        )

        serializer = FileAccessSerializer(grants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwner])
    def revoke(self, request, pk=None):
        file_obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        grant = get_object_or_404(FileAccess, file=file_obj, shared_with_id=user_id)
        grant.delete()
        return Response({'detail': 'Access revoked'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        file_obj = self.get_object()
        if file_obj.owner != request.user:
            FileAccessLog.objects.create(
                file=file_obj,
                user=request.user,
                action=FileAccessLog.Action.DOWNLOAD,
                details={'ip': request.META.get('REMOTE_ADDR', '')}
            )
        try:
            response = FileResponse(
                file_obj.file.open('rb'),
                as_attachment=True,
                filename=file_obj.filename
            )
            return response
        except Exception:
            raise Http404("File not found on disk")

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        file_obj = self.get_object()
        if file_obj.owner != request.user:
            return Response(
                {'error': 'Only owner can view logs'},
                status=status.HTTP_403_FORBIDDEN
            )
        logs = file_obj.access_logs.all().order_by('-timestamp')
        serializer = FileAccessLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        files = OsdagFile.objects.filter(owner=request.user)
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def shared(self, request):
        grants = FileAccess.objects.filter(shared_with=request.user).exclude(
            expires_at__lte=timezone.now()
        )
        file_ids = grants.values_list('file_id', flat=True)
        files = OsdagFile.objects.filter(id__in=file_ids).distinct()
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def activity(self, request):
        logs = FileAccessLog.objects.filter(
            file__owner=request.user
        ).order_by('-timestamp')[:50]
        serializer = FileAccessLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def storage_usage(self, request):
        files = OsdagFile.objects.filter(owner=request.user)
        total_bytes = files.aggregate(total=models.Sum('file_size'))['total'] or 0
        file_count = files.count()
        return Response({
            'total_bytes': total_bytes,
            'file_count': file_count,
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwner])
    def create_link(self, request, pk=None):
        file_obj = self.get_object()
        hours = request.data.get('expires_in_hours')
        expires_at = None
        if hours:
            try:
                expires_at = timezone.now() + timezone.timedelta(hours=int(hours))
            except (ValueError, TypeError):
                pass
        link = MagicLink.objects.create(
            file=file_obj,
            created_by=request.user,
            expires_at=expires_at,
        )
        return Response({
            'token': link.token,
            'expires_at': link.expires_at,
        }, status=status.HTTP_201_CREATED)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Team.objects.filter(
            models.Q(created_by=self.request.user) | models.Q(members=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTeamCreatorOrMember])
    def add_member(self, request, pk=None):
        team = self.get_object()
        if team.created_by != request.user:
            return Response(
                {'error': 'Only the creator can add members'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            team.members.add(user)
            return Response(
                {'detail': f'{email} added to team'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@perm([permissions.AllowAny])
def magic_link_download(request, token):
    link = get_object_or_404(MagicLink, token=token)
    if link.is_expired:
        return Response({'error': 'This link has expired'}, status=status.HTTP_410_GONE)
    try:
        response = FileResponse(
            link.file.file.open('rb'),
            as_attachment=True,
            filename=link.file.filename
        )
        return response
    except Exception:
        raise Http404("File not found")


@api_view(['GET'])
@perm([permissions.AllowAny])
def magic_link_info(request, token):
    link = get_object_or_404(MagicLink, token=token)
    if link.is_expired:
        return Response({'error': 'This link has expired'}, status=status.HTTP_410_GONE)
    return Response({
        'filename': link.file.filename,
        'description': link.file.description,
        'file_size': link.file.file_size,
        'uploaded_at': link.file.uploaded_at,
        'expires_at': link.expires_at,
    })
