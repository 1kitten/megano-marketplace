from app_merch.models import Product


class ComparisonService:

    @staticmethod
    def add_to_comparison_list(request, product):
        if 'comparison_list' not in request.session:
            request.session['comparison_list'] = [product.id]
        else:
            comparison_list: list = request.session['comparison_list']
            if product.id not in comparison_list:
                comparison_list.append(product.id)
                request.session['comparison_list'] = comparison_list

    @staticmethod
    def remove_from_comparison_list(request, product):
        comparison_list = request.session['comparison_list']
        comparison_list.pop(comparison_list.index(product.id))
        request.session['comparison_list'] = comparison_list

    @staticmethod
    def get_comparison_list(request):
        if 'comparison_list' not in request.session:
            request.session['comparison_list'] = []
        comparison_list = request.session['comparison_list']
        return Product.objects.filter(id__in=comparison_list)

    def get_comparison_list_count(self, request):
        return self.get_comparison_list(request=request).count()

    @staticmethod
    def clear_comparison_list(request):
        del request.session['comparison_list']


comparison_service = ComparisonService()
