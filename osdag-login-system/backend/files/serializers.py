from rest_framework import serializers
from accounts.serializers import UserSerializer
from accounts.models import User
from .models import OsdagFile, FileAccess, FileAccessLog, Team


class FileAccessSerializer(serializers.ModelSerializer):
    shared_with = UserSerializer(read_only=True)
    shared_with_email = serializers.EmailField(write_only=True, required=False)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = FileAccess
        fields = ('id', 'shared_with', 'shared_with_email', 'permission', 'expires_at',
                  'granted_at', 'is_expired')
        read_only_fields = ('id', 'granted_at')


class FileAccessLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = FileAccessLog
        fields = ('id', 'user', 'action', 'timestamp', 'details')
        read_only_fields = ('id', 'timestamp')


class OsdagFileSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    access_grants = FileAccessSerializer(many=True, read_only=True)
    logs = serializers.SerializerMethodField()

    class Meta:
        model = OsdagFile
        fields = ('id', 'owner', 'file', 'filename', 'description', 'sha256', 'file_size',
                  'uploaded_at', 'updated_at', 'access_grants', 'logs')
        read_only_fields = ('id', 'owner', 'sha256', 'file_size', 'uploaded_at', 'updated_at')

    def get_logs(self, obj):
        request = self.context.get('request')
        if request and request.user == obj.owner:
            return FileAccessLogSerializer(obj.access_logs.all(), many=True).data
        return None

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class FileUploadSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = OsdagFile
        fields = ('id', 'file', 'filename', 'description')
        read_only_fields = ('id',)


class TeamSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_emails = serializers.ListField(
        child=serializers.EmailField(), write_only=True, required=False
    )

    class Meta:
        model = Team
        fields = ('id', 'name', 'created_by', 'members', 'member_emails', 'created_at')
        read_only_fields = ('id', 'created_by', 'created_at')

    def create(self, validated_data):
        emails = validated_data.pop('member_emails', [])
        validated_data.pop('created_by', None)
        team = Team.objects.create(
            created_by=self.context['request'].user, **validated_data
        )
        team.members.add(self.context['request'].user)
        for email in emails:
            try:
                user = User.objects.get(email=email)
                team.members.add(user)
            except User.DoesNotExist:
                pass
        return team


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
