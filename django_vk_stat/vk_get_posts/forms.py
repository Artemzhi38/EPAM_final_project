import datetime

import requests
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class IdDateForm(forms.Form):
    user_page_id = forms.IntegerField(
        help_text="VKontakte id of user or group")
    start_date = forms.DateField(
        help_text="YYYY-MM-DD or MM/DD/YYYY format")

    @staticmethod
    def posts_data(user_id):
        """Func to get the last post from user's wall"""
        vk_app_token = 'TOKEN'
        wall_get_url = 'https://api.vk.com/method/wall.get'
        params = {'owner_id': user_id, 'count': 1,
                  'access_token': vk_app_token, 'v': 5.131}
        return requests.get(wall_get_url, params=params).json()

    def clean_user_page_id(self):
        data_id = self.cleaned_data['user_page_id']
        posts_data = self.posts_data(data_id)
        # Raises ValidationError if user id is 0
        if data_id == 0:
            raise ValidationError(_('Invalid id! There is no id=0 in VK'))
        # Raises ValidationError if there is no response from wall.get request
        if 'response' not in posts_data.keys():
            raise ValidationError(_('Invalid id! There is no VK profile or '
                                    'group with this id or access is denied'))
        # Raises ValidationError if there is no posts on user's wall
        if posts_data['response']['count'] == 0:
            raise ValidationError(_('Invalid id! There is no posts '
                                    'in this VK profile or group'))
        return data_id

    def clean_start_date(self):
        data_date = self.cleaned_data['start_date']
        # Raises ValidationError if start date is in future
        if data_date > datetime.date.today():
            raise ValidationError(_('Invalid date - future!'))
        # Raises ValidationError if start date is too deep in past
        if data_date.year <= 1970:
            raise ValidationError(_('Invalid date - past!'))
        return data_date

    def clean(self):
        # Raises ValidationError if there is no
        # posts on user's wall after start date
        cleaned_data = super().clean()
        user_page_id = cleaned_data.get("user_page_id")
        start_date = cleaned_data.get("start_date")
        if start_date and user_page_id:
            if (self.posts_data(user_page_id)['response']['items'][0]['date']
                    < datetime.datetime.combine(
                        start_date, datetime.time()).timestamp()):
                raise ValidationError(_(f'Invalid data! There is nothing '
                                        f'posted in this VK profile or '
                                        f'group after {start_date}'))
