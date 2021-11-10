import datetime
import time

from django.test import TestCase

from .forms import IdDateForm


class IdDateFormTest(TestCase):
    # Form labels and help text tests
    def test_id_date_form_user_page_id_label(self):
        form = IdDateForm()
        self.assertTrue(form.fields['user_page_id'].label is None or
                        form.fields['user_page_id'].label == 'user_page_id')

    def test_id_date_form_user_page_id_help_text(self):
        form = IdDateForm()
        self.assertEqual(form.fields['user_page_id'].help_text,
                         'VKontakte id of user or group')

    def test_id_date_form_start_date_label(self):
        form = IdDateForm()
        self.assertTrue(form.fields['start_date'].label is None or
                        form.fields['start_date'].label == 'start_date')

    def test_id_date_form_start_date_help_text(self):
        form = IdDateForm()
        self.assertEqual(
            form.fields['start_date'].help_text,
            'YYYY-MM-DD or MM/DD/YYYY format')

    # User page id tests
    def test_id_date_form_id_is_zero(self):
        start_date = datetime.date(1990, 11, 11)
        user_page_id = 0
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertFalse(form.is_valid())
        time.sleep(0.35)

    def test_id_date_form_id_of_closed_group(self):
        start_date = datetime.date(1990, 11, 11)
        user_page_id = -204255701
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertFalse(form.is_valid())
        time.sleep(0.35)

    def test_id_date_form_id_of_opened_profile(self):
        start_date = datetime.date(1990, 11, 11)
        user_page_id = 1
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertTrue(form.is_valid())
        time.sleep(0.35)

    def test_id_date_form_id_of_non_existent_profile(self):
        start_date = datetime.date(1990, 11, 11)
        user_page_id = 10000000000000
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertFalse(form.is_valid())
        time.sleep(0.35)

    def test_id_date_form_id_of_profile_with_empty_wall(self):
        start_date = datetime.date(1990, 11, 11)
        user_page_id = 220745065
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertFalse(form.is_valid())
        time.sleep(0.35)

    # Start date tests
    def test_id_date_form_start_date_is_future(self):
        start_date = datetime.date.today() + datetime.timedelta(days=1)
        user_page_id = 1
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertFalse(form.is_valid())
        time.sleep(0.35)

    def test_id_date_form_start_date_is_deep_in_past(self):
        start_date = datetime.date(1950, 11, 11)
        user_page_id = 1
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertFalse(form.is_valid())
        time.sleep(0.35)

    # Both params tests
    def test_id_date_form_no_posts_in_profile_after_start_date(self):
        start_date = datetime.date.today()
        user_page_id = 1
        form_data = {'start_date': start_date, 'user_page_id': user_page_id}
        form = IdDateForm(data=form_data)
        self.assertFalse(form.is_valid())
        time.sleep(0.35)
