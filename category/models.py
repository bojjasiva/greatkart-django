from distutils.command.upload import upload
from enum import unique
from unicodedata import category
from django.db import models
from django.urls import reverse 

# Create your models here.


class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)
    
    # This is to display proper plural name in admin page for model 
    class Meta:
            verbose_name = 'category'
            verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.category_name

