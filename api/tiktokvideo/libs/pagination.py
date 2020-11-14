from rest_framework import pagination, settings


class StandardResultsSetPagination(pagination.PageNumberPagination):
    """
    标准结果集分页
    """
    page_size = settings.api_settings.PAGE_SIZE or 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

