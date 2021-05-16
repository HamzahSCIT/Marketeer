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
from transformers import AdamW, get_linear_schedule_with_warmup
import torch
import random
import re
from googletrans import Translator
from google_trans_new import google_translator
import speech_recognition as sr

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
        brand = request.POST.get("name")
        length = request.POST.get("range")
        gender = request.POST.get("gender")
        female = request.POST.get("female")
        category = request.POST.get("maledd")
        adj = request.POST.get("adj")
        # if length == "short":
        #       max_length = 50
        #      length_penalty = 0.5
        # else:
            #    max_length = 300
            #   length_penalty = 1.5
        device = torch.device("cpu")
        if gender == 'male':
            output_dir = '/home/sam/python/30epochmodel'
        elif gender == 'female':
            output_dir = '/home/sam/python/femaleModel'
        model = GPT2LMHeadModel.from_pretrained(output_dir)
        tokenizer = GPT2Tokenizer.from_pretrained(output_dir)
        model.to(device)

        model.eval()

        txt = keywords + " " + adj 

        prompt = "<|startoftext|>" + txt

        generated = torch.tensor(tokenizer.encode(prompt)).unsqueeze(0)
        generated = generated.to(device)

        print(generated)

        sample_outputs = model.generate(
            generated,
            bos_token_id=random.randint(1, 30000),
            do_sample=True,
            top_k=60,
            max_length=300,
            top_p=0.65,
            num_return_sequences=1,
            length_penalty=length
        )

        for i, sample_output in enumerate(sample_outputs):
            desc = tokenizer.decode(sample_output, skip_special_tokens=True)

        if brand is not None:
            desc = multi_sub([(r'\sBRANDNAME\'s\s|\sBRANDNAME\'s$|^BRANDNAME\'s\s', ' ' + brand + '\'s '),
                                (r'\sBRANDNAME\'\s|\sBRANDNAME\'$|^BRANDNAME\'\s', ' ' + brand + '\'s '),
                                (r'\sBRANDNAME\s|\sBRANDNAME$|^BRANDNAME\s', ' ' + brand + ' '),
                                (r'\sAmerican\s|\sAmerican$|^American\s', ' Pakistani '), ],
                                desc)

    gen.insert(x, [keywords, desc])
    x + 1
    print(gen)
    context = {'desc': desc, "keywords":keywords, "name":brand, 'gen': gen}
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
            print('Sorry could not recognize your voice')

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

