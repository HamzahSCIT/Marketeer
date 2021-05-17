from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db import connection
from .models import Product, Description
from .forms import SignUpForm

from django.views.decorators.csrf import csrf_exempt
from transformers import GPT2LMHeadModel, GPT2Tokenizer, GPT2Config, GPT2LMHeadModel
import numpy as np
import re
import csv
from googletrans import Translator
from google_trans_new import google_translator
import speech_recognition as sr

from aitextgen import aitextgen
from django.conf import settings
import os

gen = [[]]
x = 0


def multi_sub(pairs, s):
    def repl_func(m):
        # only one group will be present, use the corresponding match
        return next(
            repl
            for (patt, repl), group in zip(pairs, m.groups())
            if group is not None
        )

    pattern = '|'.join("({})".format(patt) for patt, _ in pairs)
    return re.sub(pattern, repl_func, s)


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def home(request):
    count = User.objects.count()
    return render(request, 'home.html', {
        'count': count,
    })


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {
        'form': form,
    })


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


def generate_description(request):
    #function to generate description
    global keywords
    global adj
    global desc
    global text
    global brand
    global category
    global male, female

    

    if request.method == "POST":
        keywords = request.POST.get("keywords")
        brnd = request.POST.get("name")
        category = request.POST.get("male")
        adj = request.POST.get("adj")
        
        output_dir = 'C:/Users/saad/Desktop/GPT2NeoModels/MenModel'
        # output_dir = os.path.join(settings.FILES_DIR, 'MenModel')
        print(category)
        if category == 'dress':
            output_dir = 'C:/Users/saad/Desktop/GPT2NeoModels/WomenModel'


        ai = aitextgen(model_folder=output_dir, to_gpu=False)
        
        desc = ai.generate_one(
            batch_size=5,
            prompt=keywords,
            max_length=256,
            temperature=1.0,
            top_p=0.9)
        
        if brnd is not None:
            brands = []
            with open('accounts/brands.csv', encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                    brands.append(row[0])  

            for brand in brands:
                desc = re.sub(' ' + brand + ' ', ' ' + brnd + ' ', desc)
            

    gen.insert(x, [keywords, desc])
    x + 1
    print(gen)
    context = {'desc': desc, "keywords":keywords, "name":brnd, 'gen': gen}
    return render(request, 'dashboard.html', context)


def save_description(request):
    if request.method == 'POST':
        product, created = Product.objects.get_or_create(
            name=brand,
            user=request.user
        )

        description = Description(
            keywords=keywords,
            text=desc,
            product=product
        )
        description.save()
    return render(request, 'dashboard.html')


def translate(request):
    translator = Translator()
    result = translator.translate(desc, src='en', dest='ur')
    translated = result.text
    print(translated)
    context = { 'translated_text': translated }
    return render(request, 'dashboard.html', context)


def speech_to_text():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print('Speak Anything : ')
        audio = r.listen(source)

        try:
            text = r.recognize_google(audio)
            print('You said : {} '.format(text))
        except:
            print('Sorry I could not recognize your voice')

@login_required
def product_list(request):
    print(request.user.id)
    cursor = connection.cursor()
    query = '''SELECT * 
                FROM (SELECT id, username FROM public.auth_user) auth_user
                FULL OUTER JOIN (SELECT * FROM public.accounts_product) accounts_product ON auth_user.id = accounts_product.user_id
                FULL OUTER JOIN (SELECT * FROM public.accounts_description) accounts_description ON accounts_product.id = accounts_description.product_id
                WHERE user_id = %s'''
    cursor.execute(query, str(request.user.id))
    products = dictfetchall(cursor)

    return render(request, 'pro_list.html', {
        'products': products,
    })


def deleteDescription(request, product_id):
    desc_to_delete = Product.objects.get(id=product_id)
    desc_to_delete.delete()
    return HttpResponseRedirect('prod_list.html/')

