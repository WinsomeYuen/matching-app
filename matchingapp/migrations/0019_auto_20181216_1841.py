# Generated by Django 2.1.4 on 2018-12-16 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matchingapp', '0018_auto_20181213_1334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profileLike',
            field=models.ManyToManyField(to='matchingapp.Likes'),
        ),
    ]
