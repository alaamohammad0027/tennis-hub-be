from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination with enhanced response format
    """

    page_size = 50  # Default page size
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Override to include total pages and current page number
        """
        next_link = self.get_next_link()
        previous_link = self.get_previous_link()
        count = self.page.paginator.count
        total_pages = self.page.paginator.num_pages

        return Response(
            {
                "links": {
                    "next": next_link,
                    "previous": previous_link,
                },
                "count": count,
                "total_pages": total_pages,
                "current_page": self.page.number,
                # "page_size": len(data),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        """
        Override to provide proper schema for API documentation
        """
        return {
            "type": "object",
            "properties": {
                "links": {
                    "type": "object",
                    "properties": {
                        "next": {
                            "type": "string",
                            "nullable": True,
                            "format": "uri",
                            "example": "http://api.example.org/accounts/?page=4",
                        },
                        "previous": {
                            "type": "string",
                            "nullable": True,
                            "format": "uri",
                            "example": "http://api.example.org/accounts/?page=2",
                        },
                    },
                },
                "count": {
                    "type": "integer",
                    "example": 123,
                },
                "total_pages": {
                    "type": "integer",
                    "example": 3,
                },
                "current_page": {
                    "type": "integer",
                    "example": 2,
                },
                # "page_size": {
                #     "type": "integer",
                #     "example": 50,
                # },
                "results": schema,
            },
        }
