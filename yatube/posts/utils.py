from django.core.paginator import Paginator

from .constants import NUMBER_OF_POSTS


def paginator(request, post):
    paginator = Paginator(post, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
