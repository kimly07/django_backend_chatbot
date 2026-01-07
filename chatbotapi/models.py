from django.db import models

class Auth(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    is_verified = models.BooleanField(default=False)

    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    temp_username = models.CharField(max_length=100, blank=True, null=True)

    reset_token = models.CharField(max_length=512, blank=True, null=True)
    reset_token_expires = models.DateTimeField(null=True, blank=True)

    reset_otp = models.CharField(max_length=6, blank=True, null=True)
    reset_otp_created_at = models.DateTimeField(null=True, blank=True)


    key = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.email



class User(models.Model):
    
    auth = models.OneToOneField(
        Auth,
        on_delete=models.CASCADE,
        related_name="user"
    )
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class Chats(models.Model):
    auth = models.ForeignKey(
        Auth,
        on_delete=models.CASCADE,
        related_name="chats",
        db_column="auth_id",
        null=True,
    )

    name = models.CharField(max_length=128)
    is_premium = models.BooleanField(default=False)

    class Meta:
        db_table = "chats"

    def __str__(self):
        return self.name

class RoleList(models.TextChoices):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    
class Conversation(models.Model):
    chat = models.ForeignKey(
        Chats,
        on_delete=models.CASCADE,
        related_name="conversations",
        db_column="chat_id"
    )

    role = models.CharField(
        max_length=50,
        choices=RoleList.choices,
        default=RoleList.USER
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"

    def __str__(self):
        return f"{self.role} - {self.created_at}"





