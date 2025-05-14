from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def set_default_owner(apps, schema_editor):
    Task = apps.get_model('tasks', 'Task')
    User = apps.get_model('accounts', 'CustomUser')
    default_user = User.objects.first()
    if default_user:
        Task.objects.filter(owner__isnull=True).update(owner=default_user)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='owner',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.RunPython(set_default_owner),
        migrations.AlterField(
            model_name='task',
            name='owner',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]