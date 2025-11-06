from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from .models import *
from decimal import Decimal


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(active=True).order_by('-date_listed'),
        "heading": "Active Listings",
        "title": "Auctions",
        "no_watchlist": len(request.user.watchlist.all()) if request.user.is_authenticated else 0
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next')
            return HttpResponseRedirect(next_url if next_url else reverse('index'))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password.",
                "next": request.POST.get("next", "")
            })
    else:
        return render(request, "auctions/login.html", {
            "next": request.GET.get("next", "")
        })


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })

        
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required(login_url='/login')
def create(request):
    if request.method == "POST":
        try:
            price = Decimal(request.POST["starting_bid"])
        except ValueError:
            return render(request, "auctions/create.html", {
                "categories": Category.objects.all(),
                "message": "Invalid price.",
                "no_watchlist": len(request.user.watchlist.all())
            })
        
        item = Listing(
            title=request.POST["title"],
            description=request.POST["description"],
            owner=request.user,
            starting_bid=price,
            image=request.POST.get("image", None)
        )

        category_id = request.POST.get("category")
        if category_id:
            try:
                cat = Category.objects.get(id=category_id)
                item.category = cat
            except Category.DoesNotExist:
                return render(request, "auctions/create.html", {
                    "categories": Category.objects.all(),
                    "message": "Trying to be smart huh? Invalid category.",
                    "no_watchlist": len(request.user.watchlist.all())
                })

        try:
            item.full_clean()
            item.save()
        except ValidationError as e:
            return render(request, "auctions/create.html", {
                "categories": Category.objects.all(),
                "message": ' '.join(' '.join(v) for v in e.message_dict.values()),
                "no_watchlist": len(request.user.watchlist.all())
            })
        
        return HttpResponseRedirect(reverse("index"))
        

    return render(request, "auctions/create.html", {
        "categories": Category.objects.all(),
        "no_watchlist": len(request.user.watchlist.all())
    })


def listing(request, listingid):
    try:
        item = Listing.objects.get(id=listingid)
        price = item.starting_bid
        bids = increase = 0
        in_watchlist = request.user.watchlist.filter(pk=item.id).exists() if request.user.is_authenticated else False
        message = ""
        alert_type = "danger"

        if item.current_bid:
            price = item.current_bid.price
            bids = len(item.bids.all())
        
        if request.method == "POST":
            try:
                if bid := request.POST.get("bid"):
                    if request.user == item.owner:
                        raise ValidationError("You cannot bid on your own listing.")
                    
                    bid = Decimal(bid)
                    if bid <= price:
                        raise ValidationError("You can only bid for the value greater than the current price.")
                    
                    bid_made = Bid(user=request.user, price=bid, listing_id=item)
                    bid_made.full_clean()
                    bid_made.save()

                    item.current_bid = bid_made
                    item.save()

                    bids += 1
                    price = bid
                    message = "You have successfully placed your bid!"
                    alert_type = "success"
                elif comment_text := request.POST.get("comment"):
                    comment = Comment(user=request.user, listing=item, text=comment_text)
                    comment.full_clean()
                    comment.save()

                    message = "Comment posted."
                    alert_type = "primary"
                elif request.POST.get("watchlist"):
                    if in_watchlist:
                        request.user.watchlist.remove(item)
                        message = "Listing removed from watchlist."
                    else:
                        request.user.watchlist.add(item)
                        message = "Listing added to watchlist."
                    alert_type = "light"
                    in_watchlist = not in_watchlist
                else:
                    if request.user != item.owner:
                        raise ValidationError("Unauthorized user.")
                    
                    item.active = False
                    if bids:
                        item.winner = item.current_bid.user
                    
                    item.full_clean()
                    item.save()
            except Exception as e:
                message = ' '.join(' '.join(v) for v in e.message_dict.values())

        if item.current_bid:
            increase = round((item.current_bid.price/item.starting_bid - 1) * 100, 2)

        comments = item.comments.all().order_by('-timestamp')

        return render(request, "auctions/listing.html", {
            "listing": item,
            "number_of_bids": bids,
            "increase": increase,
            "price": price,
            "message": message,
            "alert_type": alert_type,
            "comments": comments,
            "no_of_comments": len(comments),
            "watchlist": in_watchlist,
            "no_watchlist": len(request.user.watchlist.all()) if request.user.is_authenticated else 0
        })
    except Listing.DoesNotExist:
        return render(request, "auctions/listing.html", {
            "message": "404 Listing not found.",
            "alert_type": "danger",
            "no_watchlist": len(request.user.watchlist.all()) if request.user.is_authenticated else 0
        })


def category_main(request):
    return render(request, "auctions/index.html", {
        "categories": Category.objects.all().order_by("name"),
        "listings": Listing.objects.filter(category=None).order_by("-date_listed"),
        "category": True,
        "title": "Categories",
        "heading": "Active uncategorized items",
        "no_watchlist": len(request.user.watchlist.all()) if request.user.is_authenticated else 0
    })


def category(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        return render(request, "auctions/index.html", {
            "listings": Listing.objects.filter(active=True, category=category).order_by("-date_listed"),
            "title": category.name,
            "heading": f"Active listings in {category.name}",
            "no_watchlist": len(request.user.watchlist.all()) if request.user.is_authenticated else 0
        })
    except Category.DoesNotExist:
        return render(request, "auctions/index.html", {
        "categories": Category.objects.all().order_by("name"),
        "listings": Listing.objects.filter(active=True, category=None).order_by("-date_listed"),
        "category": True,
        "title": "Categories",
        "heading": "Active uncategorized Items",
        "message": "No such category",
        "no_watchlist": len(request.user.watchlist.all()) if request.user.is_authenticated else 0
    })


@login_required(login_url='/login')
def watchlist(request):
    watch = request.user.watchlist.all().order_by("-date_listed")
    return render(request, "auctions/index.html", {
        "listings": watch,
        "title": f"{request.user}'s watchlist",
        "heading": "Your watchlist",
        "watchlist": True,
        "no_watchlist": len(watch) 
    })