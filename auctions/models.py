from django.contrib.auth.models import AbstractUser
from django.db import models
from .validate import validate_image_url


class User(AbstractUser):
    watchlist = models.ManyToManyField('Listing', blank=True)


class Category(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name}"


class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing_id = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name="bids")
    price = models.DecimalField(max_digits=11, decimal_places=2)

    def __str__(self):
        return f"{self.price} on {self.listing_id.title} by {self.user}"


class Listing(models.Model):
    title = models.CharField(max_length=40)
    description = models.CharField(max_length=250)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    starting_bid = models.DecimalField(max_digits=11, decimal_places=2)
    image = models.URLField(blank=True, null=True, validators=[validate_image_url])
    category = models.ForeignKey(Category, on_delete=models.PROTECT, blank=True, null=True, related_name="listings")
    current_bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True)
    date_listed = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} by {self.owner}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=100)

    def __str__(self):
        return f"\"{self.text}\" on {self.listing}"
