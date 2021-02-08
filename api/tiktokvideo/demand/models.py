from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models


class VideoNeeded(models.Model):
    uid = models.ForeignKey(
        'users.Users',
        to_field='uid',
        on_delete=models.CASCADE,
        related_name='video_needed'
    )
    TO_PUBLISH, TO_CHECK, ON_GOING, DONE, EXCEPTION = range(5)
    status = models.PositiveSmallIntegerField(
        default=0,
        choices=(
            (TO_PUBLISH, '未发布'),
            (TO_CHECK, '待审核'),
            (ON_GOING, '进行中'),
            (DONE, '已完成'),  # 没用到
            (EXCEPTION, '异常'),  # 没用到
        )
    )
    reject_reason = models.TextField(
        verbose_name='拒绝原因',
        null=True
    )

    # needed desc #
    title = models.CharField(
        verbose_name='标题',
        max_length=128,
        blank=True
    )
    industries = models.CharField(
        verbose_name='行业',
        max_length=64,
    )
    category = models.ForeignKey(
        'config.GoodsCategory',
        on_delete=models.DO_NOTHING,
        related_name='video_needed'
    )
    goods_title = models.CharField(
        verbose_name='标题',
        max_length=128,
        blank=True
    )
    goods_link = models.URLField(
        verbose_name='商品链接',
        max_length=3000
    )
    goods_images = models.URLField(
        verbose_name='商品主图',  # 来自于goods_link解析
        max_length=3000,
    )
    TB, JD, KL, DY = range(4)
    CHANEL = (
        (TB, "淘宝"),
        (JD, "京东"),
        (KL, "网易考拉"),
        (DY, "抖音小店"),
    )
    goods_channel = models.PositiveSmallIntegerField(
        verbose_name='商品来源',
        default=TB,
        choices=CHANEL
    )
    attraction = models.TextField(
        verbose_name='商品卖点',
        blank=True,
        null=True
    )
    video_num_needed = models.PositiveIntegerField(
        verbose_name='拍摄视频数',
        default=0
    )
    video_num_remained = models.PositiveIntegerField(
        verbose_name='剩余数(视频数)',
        default=0,
        db_index=True
    )
    is_return = models.BooleanField(
        verbose_name='是否返样',
        default=False
    )
    return_ways = models.PositiveSmallIntegerField(
        verbose_name='返回方式',
        default=0,
        choices=(
            (0, '顺丰到付'),
            (1, '现付'),
        )
    )

    # 需要在订单流程中维护这几个字段
    # order desc
    order_slice_num = models.PositiveSmallIntegerField(
        verbose_name='订单分片数',
        default=0
    )
    order_video_slice = ArrayField(
        JSONField(
            verbose_name='订单的视频数分片',
        ),
        default=list
    )
    order_num_remained = models.PositiveSmallIntegerField(
        verbose_name='剩余申请数(订单数)',
        default=0
    )

    # receiver desc
    receiver_name = models.CharField(
        verbose_name='返样收货人名字',
        max_length=64,
        null=True
    )
    receiver_phone = models.CharField(
        verbose_name='返样收货人电话',
        max_length=64,
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

    # video desc #
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
        default=None,
        null=True,
        choices=(
            (0, '无要求'),
            (1, '男模特'),
            (2, '女模特'),
            (3, '男+女模特'),
        )
    )
    model_occur_rate = models.PositiveSmallIntegerField(
        verbose_name='模特出场率',
        default=None,
        null=True,
        choices=(
            (0, '无要求'),
            (1, '>10%'),
            (2, '>20%'),
            (3, '>30%'),
            (4, '>50%'),
        )
    )
    model_age_range = models.PositiveSmallIntegerField(
        verbose_name='模特年龄范围',
        default=None,
        null=True,
        choices=(
            (0, '无要求'),
            (1, '婴幼儿'),
            (2, '儿童/少年'),
            (3, '18-35岁'),
            (4, '35-55岁'),
        )
    )
    model_figure = models.PositiveSmallIntegerField(
        verbose_name='模特身材',
        default=None,
        null=True,
        choices=(
            (0, '无要求'),
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
    platform_desc = models.TextField(
        verbose_name='平台说明',
        null=True,
        blank=True,
        default=None
    )
    example1 = models.TextField(
        verbose_name='参考视频1',
        null=True,
        blank=True
    )
    example2 = models.TextField(
        verbose_name='参考视频2',
        null=True,
        blank=True
    )
    example3 = models.TextField(
        verbose_name='参考视频3',
        null=True,
        blank=True
    )

    # time desc #
    create_time = models.DateTimeField(
        auto_now_add=True
    )
    update_time = models.DateTimeField(
        auto_now=True
    )
    check_time = models.DateTimeField(
        verbose_name='审核时间',
        null=True
    )
    done_time = models.DateTimeField(
        verbose_name='完成时间',
        null=True
    )
    publish_time = models.DateTimeField(
        verbose_name='最近一次的发布审核时间',
        null=True
    )
    non_publish_time = models.DateTimeField(
        verbose_name='最近一次的下架时间',
        null=True
    )

    class Meta:
        verbose_name = '短视频需求单'
        verbose_name_plural = verbose_name
        db_table = 'VideoNeeded'
        ordering = ('-create_time',)


class HomePageVideo(models.Model):
    creator = models.ForeignKey(
        'users.Users',
        to_field='uid',
        related_name='home_page_video',
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )

    video_link = models.URLField(
        verbose_name='视频链接',
        max_length=3000
    )
    title = models.CharField(
        verbose_name='标题',
        max_length=128,
        null=True
    )
    category = models.ForeignKey(
        'config.GoodsCategory',
        on_delete=models.DO_NOTHING,
        related_name='home_video',
        null=True
    )
    is_show = models.BooleanField(
        verbose_name='是否展示',
        default=True
    )
    like = models.PositiveIntegerField(
        verbose_name='点赞数',
        default=0
    )
    comment = models.PositiveIntegerField(
        verbose_name='评论数',
        default=0
    )
    share_num = models.PositiveIntegerField(
        verbose_name='分享数',
        default=0
    )

    # video desc #
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
            (0, '无要求'),
            (1, '男模特'),
            (2, '女模特'),
            (3, '男+女模特'),
        )
    )
    model_occur_rate = models.PositiveSmallIntegerField(
        verbose_name='模特出场率',
        default=0,
        choices=(
            (0, '无要求'),
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
            (0, '无要求'),
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
            (0, '无要求'),
            (1, '偏瘦'),
            (2, '中等'),
            (3, '偏肥/大码'),
        )
    )

    # time desc
    create_time = models.DateTimeField(
        auto_now_add=True
    )
    update_time = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "首页展示视频"
        verbose_name_plural = verbose_name
        db_table = "HomePageVideo"
        ordering = ('-create_time',)

