from rest_framework.pagination import PageNumberPagination


class FlexPageNumberPagination(PageNumberPagination):
    """
    Extends the default PageNumberPagination so the client can request a
    specific page size via ?page_size=N (capped at max_page_size).

    Used as the global DEFAULT_PAGINATION_CLASS so every ModelViewSet
    automatically supports both ?page=N and ?page_size=N.
    """
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200
