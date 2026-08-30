# 认识胸部

以美学、健康与自主选择为主题的静态科普网站，包含 6 个专栏与 40 篇文章，优先适配手机阅读。

- 网站 https://breast.meilipai.vip/
- 隐私声明 https://breast.meilipai.vip/privacy.html
- 开源说明 https://breast.meilipai.vip/open-source.html
- 维护者 sooogooo

本站用于公众健康教育，不构成医疗建议，不替代专业面诊与检查。

## 运行

网站没有运行时框架、数据库、账号、追踪脚本或表单接口，静态服务器即可提供页面。

```sh
python -m http.server 8000
```

在浏览器中访问 `http://localhost:8000/`。部署需要位于域名根路径，资源与公共导航使用根相对 URL。

## 结构

- 根目录 HTML 为首页、专栏、隐私声明、开源说明和 404 页面。
- `jichu/`、`jiankang/`、`augmentation/`、`reduction/`、`styling/`、`guide/` 为文章页面。
- `assets/base.css` 为基础样式，`assets/visual.css` 为图文样式，`assets/mobile.css` 为手机与公共信息页样式。
- `assets/site.js` 处理原生菜单的增强行为与主动分享，`assets/visual.js` 处理阅读进度。
- `assets/img/` 包含全站配图、逐篇头图和轻量缩略图。
- `templates/` 集中维护页脚和信息页正文；`scripts/sync_site.py` 同步生成公共部分。
- `tests/` 检查公共页脚、导航、链接、图片、标题与隐私相关页面约定。

## 修改与检查

```sh
python -m pip install -r requirements-dev.txt
python scripts/sync_site.py
python -m unittest discover -s tests -v
```

修改文章正文可直接编辑对应 HTML。修改页脚或政策正文后运行同步脚本。同步脚本不改写文章正文或卡片内容。

标题不使用英文或中文冒号。有关机构选择的表述统一使用“三级综合医院或者设施齐备的专科医院”。

## 部署

只需上传页面、`assets/`、专栏目录、`favicon.ico`、`robots.txt`、`sitemap.xml` 和 `llms.txt`，并将服务器的 404 页面设为 `/404.html`。

不要把 `.git/`、访问令牌、服务器配置、日志、备份和私钥部署到公开目录。仓库不包含生产凭据、日志或服务器配置；也没有自动生产发布工作流。

复用此站时请替换域名、机构名称、标志、备案号、联系方式和隐私声明，不能沿用本站身份信息作为其他站点的资质证明。

## 授权与内容

代码部分采用 [MIT 许可](LICENSE)。文章、图片、品牌与机构标识另见 [内容与素材说明](CONTENT-LICENSE.md)，不随代码自动获得 MIT 授权。

配图含 AI 辅助生成的科普示意，不代表真实患者、医生、设施或医疗效果。

## 联系

sooogooo@139.com · 微信 @sooogooo

问题反馈请勿提交患者信息、病历、个人敏感资料、访问令牌或服务器密钥。
