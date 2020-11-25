from django.contrib.postgres.fields import ArrayField
from django.db import models

# Create your models here.


class VideoNeeded(models.Model):
    uid = models.ForeignKey(
        'users.Users',
        to_field='uid',
        on_delete=models.CASCADE,
        related_name='video_needed'
    )
    title = models.CharField(
        verbose_name='标题',
        max_length=128,
        blank=True
    )
    industries = models.CharField(
        verbose_name='行业',
        max_length=64,
        blank=True,
        null=True
    )
    category = models.CharField(
        verbose_name='商品品类',
        max_length=64
    )
    goods_link = models.UUIDField(
        verbose_name='商品链接',
        max_length=3000
    )
    attraction = models.TextField(
        verbose_name='商品卖点',
        blank=True,
        null=True
    )
    num_needed = models.PositiveIntegerField(
        verbose_name='拍摄视频数',
        default=0
    )
    num_remained = models.PositiveIntegerField(
        verbose_name='剩余数',
        default=0
    )
    video_num_split = ArrayField(
        models.PositiveIntegerField(
            verbose_name='视频数分片',
            null=True
        ),
        default=list
    )
    is_return = models.BooleanField(
        verbose_name='是否返样',
        default=False
    )
    receiver_name = models.CharField(
        verbose_name='返样收货人名字',
        null=True
    )
    receiver_phone = models.CharField(
        verbose_name='返样收货人电话',
        null=True
    )
    receiver_province = models.CharField(
        verbose_name='返样所在地省',
        max_length=128,
        null=True
    )
    receiver_city = models.CharField(
        verbose_name='返样所在地市',
        max_length=128,
        null=True
    )
    receiver_district = models.CharField(
        verbose_name='返样所在地地区',
        max_length=128,
        null=True
    )
    receiver_location = models.CharField(
        verbose_name='返样具体地址',
        max_length=128,
    )
    video_size = models.PositiveSmallIntegerField(
        verbose_name='视频尺寸',
        default=0,
        choices=(
            (0, '3: 4 【竖屏】'),
            (1, '9: 16 【竖屏】'),
            (2, '16: 9 【横屏】'),
        )
    )
    clarity = models.PositiveSmallIntegerField(
        verbose_name='视频清晰度',
        default=0,
        choices=(
            (0, '720p标清及以上'),
            (1, '1080p高清及以上'),
        )
    )
    model_needed = models.PositiveSmallIntegerField(
        verbose_name='模特需求类型',
        default=0,
        choices=(
            (0, '否'),
            (1, '男模特'),
            (2, '女模特'),
            (3, '男+女模特'),
        )
    )
    model_occur_rate = models.PositiveSmallIntegerField(
        verbose_name='模特出场率',
        default=0,
        choices=(
            (0, '未选择'),
            (1, '>10%'),
            (2, '>20%'),
            (3, '>30%'),
            (4, '>50%'),
        )
    )
    model_age_range = models.PositiveSmallIntegerField(
        verbose_name='模特年龄范围',
        default=0,
        choices=(
            (0, '未选择'),
            (1, '婴幼儿'),
            (2, '儿童/少年'),
            (3, '18-35岁'),
            (4, '35-55岁'),
        )
    )
    model_figure = models.PositiveSmallIntegerField(
        verbose_name='模特身材',
        default=0,
        choices=(
            (0, '未选择'),
            (1, '偏瘦'),
            (2, '中等'),
            (3, '偏肥/大码'),
        )
    )
    desc = models.TextField(
        verbose_name='其他说明',
        null=True,
        blank=True
    )
    example1 = models.TextField(
        verbose_name='同行视频1',
        null=True,
        blank=True
    )
    example2 = models.TextField(
        verbose_name='同行视频2',
        null=True,
        blank=True
    )
    example3 = models.TextField(
        verbose_name='同行视频3',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = '短视频需求单'
        verbose_name_plural = verbose_name
        db_table = 'VideoNeeded'
