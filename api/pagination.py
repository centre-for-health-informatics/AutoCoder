from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from rest_framework.utils.urls import remove_query_param, replace_query_param


class CustomPageNumberPagination(PageNumberPagination):

    page_size_query_param = 'size'  # items per page

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('per_page', len(self.page)),
            ('page', self.page.number),
            ('total', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('next', self.get_next_params()),
            ('previous', self.get_previous_link()),
            ('data', data)
        ]))

    def get_next_params(self):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        page_size = len(self.page)
        next_params = f'?{self.page_query_param}={page_number}&{self.page_size_query_param}={page_size}'

        return next_params

    def get_previous_params(self):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        page_size = len(self.page)
        next_params = f'?{self.page_query_param}={page_number}&{self.page_size_query_param}={page_size}'

        return next_params
