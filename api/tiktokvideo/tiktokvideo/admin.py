SIMPLEUI_STATIC_OFFLINE = True  # 离线模式（指定simpleui是否以脱机模式加载静态资源，为True的时候将默认从本地读取所有资源，即使没有联网一样可以。适合内网项目）
SIMPLEUI_HOME_QUICK = False  # 快速操作
SIMPLEUI_HOME_INFO = False  # 服务器信息
SIMPLEUI_DEFAULT_ICON = False  # 默认图标
SIMPLEUI_LOGIN_PARTICLES = False  # 关闭登录页粒子动画
SIMPLEUI_HOME_TITLE = '松鼠短视频'

# 默认主题
SIMPLEUI_DEFAULT_THEME = 'ant.design.css'
# SIMPLEUI_DEFAULT_THEME = 'layui-icon-rate'
# 首页
# SIMPLEUI_HOME_PAGE = ''
# 最近动作
SIMPLEUI_HOME_ACTION = True

SIMPLEUI_CONFIG = \
    {
        'system_keep': False,
        'dynamic': True,  # 设置是否开启动态菜单, 默认为False. 如果开启, 则会在每次用户登陆时动态展示菜单内容
        'menus':
            [

                {
                    'app': 'users',
                    'name': '用户管理',
                    'icon': 'fa fa-users',
                    'models': [
                        {
                            'name': '用户管理',
                            'url': '/admin/users/users/',
                            'icon': 'fas fa-baby'
                        },
                        {
                            'name': '商家信息',
                            'url': '/admin/users/userbusiness/',
                            'icon': 'fas fa-baby'
                        },
                    ]
                },
                {
                    'app': 'CustomerService',
                    'name': '联系客服',
                    'icon': 'fa fa-users',
                    'url': '/admin/config/customerservice/',
                },

            ]
    }
