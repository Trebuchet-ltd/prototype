from rest_framework import serializers
from .models import ImageModel, CartModel
from .models import Product
from .models import Tokens, CartItem, TransactionDetails, \
    Orders, OrderItem, Addresses, RecipeBox, Quantity, NutritionQuantity, Nutrition, Category, Reviews


class GetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = [
            'title', 'mainimage', 'cleaned_image'
        ]


class GetNutritionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nutrition
        fields = ['name']


class GetNutritionQuantitySerializer(serializers.ModelSerializer):
    nutrition = GetNutritionSerializer(many=False)

    class Meta:
        model = NutritionQuantity
        fields = ['quantity', 'nutrition']


class GetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'code', 'category', 'color', 'icon']


class GetProductSerializer(serializers.ModelSerializer):
    images = GetImageSerializer(many=True, required=False)
    nutrition = GetNutritionQuantitySerializer(many=True, read_only=True)
    meat = GetCategorySerializer(read_only=True, many=False)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'code', 'description', 'short_description', 'price', 'stock',
            'meat', 'images', 'bestSeller', "weight", 'rating',
            'weight_variants', 'pieces', 'serves', 'can_be_cleaned', 'cleaned_price', "discount", 'recipe_box',
            'nutrition', 'product_gst_percentage', 'product_rate_with_gst', 'type_of_quantity'
        ]


class GetShadowProductSerializer(serializers.ModelSerializer):
    images = GetImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'short_description', 'price', 'stock',
            'meat', 'images', 'bestSeller', 'rating',
            "discount",
        ]


class GetRecipeProductSerializer(serializers.ModelSerializer):
    images = GetImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'short_description',
            'meat', 'images', 'bestSeller', 'rating',

        ]


class GetQuantitySerializer(serializers.ModelSerializer):
    product = GetRecipeProductSerializer(many=False, read_only=True, )

    class Meta:
        model = Quantity
        fields = [
            'product', 'quantity'
        ]


class GetRecipeBoxSerializer(serializers.ModelSerializer):
    items = GetQuantitySerializer(many=True, read_only=True)
    shadow_product = GetShadowProductSerializer(many=False, read_only=True)

    class Meta:
        model = RecipeBox
        fields = [
            'shadow_product', 'video_url', 'items',
        ]


class GetReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Reviews
        fields = [
            'id', 'user', 'title', 'content', 'item', 'stars', 'date', 'last_edit'
        ]
        # extra_kwargs = {
        #     'user': {'read_only': True},
        # }


class GetReviewSerializerWithoutUser(serializers.ModelSerializer):
    class Meta:
        model = Reviews
        fields = [
            'title', 'content', 'stars',
        ]


class GetTokensSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tokens
        fields = [
            'user', 'private_token', 'invite_token', 'invited', 'points',
            'reviews', 'total_points_yet', 'first_purchase_done', 'amount_saved'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    item = GetProductSerializer(read_only=True, required=False, many=False)

    class Meta:
        model = CartItem
        fields = [
            'id', 'item', 'quantity', 'cart', 'weight_variants', 'is_cleaned'
        ]
        extra_kwargs = {
            'cart': {'read_only': True},
        }


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = CartModel
        fields = [
            'id', 'total', "items"
        ]


class TransactionDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionDetails
        fields = [
            "id", "payment_status", 'payment_id'
        ]


class GetAddressSerializer(serializers.ModelSerializer):
    class Meta:
        ordering = ['id']
        model = Addresses
        fields = [
            'id', 'name', 'address', 'pincode', 'state', 'phone', 'latitude', 'longitude', "delivery_charge", 'gst'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    item = GetProductSerializer(read_only=True, required=False, many=False)

    class Meta:
        model = OrderItem
        fields = [
            'item', 'quantity', 'weight_variants', 'is_cleaned'
        ]


class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer(many=True, read_only=True, required=False)
    address = GetAddressSerializer(read_only=True, required=False)
    transaction = TransactionDetailsSerializer(read_only=True, many=False, required=False)

    class Meta:
        model = Orders
        fields = [
            'id', 'user', 'total', 'date', 'time',
            'address', 'status', 'order_item',
            'transaction', 'used_points'
        ]
