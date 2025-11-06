from django.contrib import admin
from .models  import *


class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "category", "active", "starting_bid", "current_bid", "date_listed")


class UserAdmin(admin.ModelAdmin):
    list_display = ("id",  "username", "email", "date_joined", "last_login")
    filter_horizontal = ("watchlist",)


class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "listing_id", "price")


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "user", "listing", "timestamp")


# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Category, CategoryAdmin)
