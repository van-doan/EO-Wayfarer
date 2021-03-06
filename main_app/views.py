from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Author, Article, Comment, Location
from main_app.forms import Article_Form, Profile_Form, Comment_Form, Search_Form
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
import psycopg2 # this will help us connect to our location DB


#-----------------------------------------------------------------------------#
#                              A D M I N / A U T H                            #
#-----------------------------------------------------------------------------#
def signup(request):
    error_message=''

    if request.method == 'POST':
        user_form = UserCreationForm(data = {
            'username':request.POST['username'], 
            'password1': request.POST['password1'], 
            'password2': request.POST['password2']})
        if user_form.is_valid():
            user = user_form.save()
            
            #new_form.user_id = user.id 

            login(request, user)
            return redirect('authors_index') 
        else:
            error_message='Invalid sign-up try again'
    else:
        user_form=UserCreationForm()

    context = {'user_form': user_form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)

def loginError (request):
    return render(request, 'home.html')

#-----------------------------------------------------------------------------#
#                                S T A T I C                                  #
#-----------------------------------------------------------------------------#
def home (request):
    login_form = AuthenticationForm()
    return render(request, 'home.html', {'form': login_form})

def about(request):
    return render(request, 'about.html')


#-----------------------------------------------------------------------------#
#                             L O C A T I O N S                               #
#-----------------------------------------------------------------------------#
def location_index(request):
    location = Location.objects.all()
    # if request.method == 'POST':
    #     search_form = Search_Form(request.POST)
    #     if search_form.is_valid():
    #         sel_id = search_form.cleaned_data.get('location')
    #         search_form.save()
    #         return print(sel_id)
    #         # return redirect('location_detail', sel_id=sel_id)
    # else:
    #     search_form = Search_Form()

    context = {'location': location}

    return render(request, 'locations/index.html', context)

@login_required(login_url= 'loginError')
def location_detail(request, location_id):
    location = Location.objects.get(id=location_id)    
    context = {
            'location': location,
    }

    return render(request, 'locations/detail.html', context)


#-----------------------------------------------------------------------------#
#                                 A U T H O R S                               #
#-----------------------------------------------------------------------------#
@login_required(login_url= 'loginError')
def authors_index(request):
    articles = Article.objects.filter(author=request.user.id)
    author = Author.objects.filter(user=request.user)
    context = { 'articles' : articles, 'user' : request.user, 'author' : author }
    return render(request, 'authors/index.html', context)

@login_required(login_url= 'loginError')
def author_edit(request, user_id):
    error_message=''
    # authors = Author.objects.get(id=user_id)
    if request.method == 'POST':
        author_form = Profile_Form(request.POST, request.FILES, instance = request.user.author)
        if author_form.is_valid():
            author_form.save()
            return redirect('authors_index')
        else:
            error_message='Invalid sign-up try again'
    else: 
        author_form = Profile_Form(instance=request.user.author)
    
        context = {'author_form': author_form}

        return render(request, 'authors/edit.html', context)

        
#-----------------------------------------------------------------------------#
#                                A R T I C L E S                              #
#-----------------------------------------------------------------------------#
"""Show all articles."""
def articles_index(request):
    articles = Article.objects.order_by('created_on')
    context = {'articles': articles}
    return render(request, 'articles/index.html', context)

"""Show a single article."""
@login_required(login_url= 'loginError')

def article_detail(request, article_id):
    article = Article.objects.get(id=article_id)
    comments = article.comments.filter(active=True)
    new_comment = None

    if request.method == 'POST':
        comment_form = Comment_Form(data=request.POST)
        if comment_form.is_valid():

            new_comment = comment_form.save(commit=False)
            new_comment.article = article
            new_comment.save()
    
    else:
        comment_form = Comment_Form()

    context = {
        'article': article,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form
    }

    return render(request, 'articles/detail.html', context)

"""Adds an Article"""
@login_required(login_url= 'loginError')
def article_add(request, location_id):
    location = Location.objects.get(id = location_id)
    if request.method == 'POST':
        new_form = Article_Form(request.POST)
        if new_form.is_valid():
            new_article = new_form.save(commit=False)
            new_article.author_id = request.user.id
            new_article.location = location
            new_article.save()

            return redirect('location_detail', location_id)
    else: 
        new_form = Article_Form()
        context = {
            'new_form': new_form,
            'location': location
        }
        return render(request, 'articles/add.html', context)

"""Edit an Article"""
# We want to identify the article by its 'id'. 
# When a user presses a button to "Edit", this will trigger a POST).
# We want to get the selected Article object, render the form to our
# HTML template. If the user fulfills the form's requirements before
# submitting the form, it's saved and they'll be redirected.
@login_required(login_url= 'loginError')
def edit_article(request, article_id):
    sel_article = Article.objects.get(id=article_id)
    # Naming convention: "sel" => selected #
    if request.method == 'POST':
        art_form = Article_Form(request.POST, instance=sel_article)
        if art_form.is_valid():
            updated_article = art_form.save()
            return redirect('article_detail', updated_article.id)
    else:
        art_form = Article_Form(instance=sel_article)
        context = {
            'article': sel_article,
            'art_form': art_form
        }
        return render(request, 'articles/edit.html', context)

"""Delete an Article"""
# We want to identify the article by its 'id'. 
# When a user presses a button to "Delete", this will trigger a POST).
# We want to get the selected Article object and delete it
# then redirect them to the main location_index
@login_required(login_url= 'loginError')
def delete_article(request, article_id):
    if request.method == 'POST':
        Article.objects.get(id=article_id).delete()

        return redirect('location_index')


#-----------------------------------------------------------------------------#
#                                C O M M E N T S                              #
#-----------------------------------------------------------------------------#

def edit_comment(request, comment_id):
    """Edit an existing comment."""
    comment = Comment.objects.get(id=comment_id)
    article = comment.article

    if request.method != 'POST':
        # Initial request; pre-fill form with current comment.
        form = Comment_Form(instance=comment)
    else:
        # POST data submitted; process data.
        form = Comment_Form(instance=comment, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('article_detail', article_id=article.id)

    context = {'comment': comment, 'article': article, 'form': form}
    return render(request, 'comments/edit.html', context)

def delete_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    article = comment.article

    if request.method == 'POST':
        Comment.objects.get(id=comment_id).delete()

        return redirect('article_detail', article_id=article.id)
