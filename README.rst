=====================
VK statistics
=====================
| For application to work it is required to pass your VK api token to:
| - django_vk_stat/django_vk_stat/vk_get_posts/views.py 258 line
| - django_vk_stat/django_vk_stat/vk_get_posts/forms.py 18 line
|
| 1 In command line with activated python interpreter(Python 3.8 recommended) run:
|   pip install -r requirements.txt
|
| 2 To apply basic migrations run server cd to django_vk_stat/django_vk_stat/ and run:
|   python manage.py migrate
|   python manage.py runserver
|
| 3 In your browser go to the 127.0.0.1:8000
|
| 4 Type required params(user id and starting date) into the form and press 'Submit' button
|
| 5 Now you are on the results page. Here you can see graphs with statistics for every hour/day of the week/months/year in which posts were posted.
| To download CSV-file with data about every post push 'Download CSV' button at the bottom of the page.
|