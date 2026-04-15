<!-- # Lin-CMS-Flask -->

<h1 align="center">
  <a href="https://doc.cms.talelin.com/">
  <img src="https://doc.cms.talelin.com/left-logo.png" width="250"/></a>
  <br>
  Lin-CMS-Flask
</h1>

<h4 align="center">一个简单易用的CMS后端项目 | <a href="https://doc.cms.talelin.com/" target="_blank">Lin-CMS-Flask</a></h4>

<p align="center">
  <a href="https://flask.palletsprojects.com/en/3.1.x/" rel="nofollow">
  <img src="https://img.shields.io/badge/Flask-3.1.3-green.svg" alt="Flask version" data-canonical-src="https://img.shields.io/badge/Flask-3.1.3-green.svg" style="max-width:100%;"></a>
    <a href="https://www.python.org/" rel="nofollow">
    <img src="https://img.shields.io/badge/python->=3.10,<3.15-red.svg" alt="Python version" data-canonical-src="https://img.shields.io/badge/python->=3.10,<3.15-red.svg" style="max-width:100%;">
    </a>
      <a href="https://doc.cms.talelin.com/" rel="nofollow"><img src="https://img.shields.io/badge/license-MIT-skyblue.svg" alt="LISENCE" data-canonical-src="https://img.shields.io/badge/license-MIT-skyblue.svg" style="max-width:100%;"></a>
</p>

<blockquote align="center">
  <em>Lin-CMS</em> 是林间有风团队经过大量项目实践所提炼出的一套<strong>内容管理系统框架</strong>。<br>
 Lin-CMS 可以有效的帮助开发者提高 CMS 的开发效率。
</blockquote>

<p align="center">
  <a href="#简介">简介</a>&nbsp;|&nbsp;<a href="https://doc.cms.talelin.com/start/flask/">快速起步</a>&nbsp;
</p>

## 简介

### 什么是 Lin CMS？

Lin-CMS 是林间有风团队经过大量项目实践所提炼出的一套**内容管理系统框架**。Lin-CMS 可以有效的帮助开发者提高 CMS 的开发效率。

本项目是 Lin CMS 后端的 Flask 实现，需要前端？请访问[前端仓库](https://github.com/TaleLin/lin-cms-vue)。

### 线上 demo

[http://face.cms.talelin.com/](http://face.cms.talelin.com/)

### QQ 交流群

QQ 群号：643205479

<img class="QR-img" width="258" height="300" src="http://i1.sleeve.talelin.com/qq-group.jpeg">

### 微信公众号

微信搜索：林间有风

<img class="QR-img" src="http://i1.sleeve.talelin.com/wechat-account.jpeg">

### Lin CMS 的特点

Lin CMS 的构筑思想是有其自身特点的。

#### Lin CMS 是一个前后端分离的 CMS 解决方案

这意味着，Lin CMS 既提供后台的支撑，也有一套对应的前端系统，当然双端分离的好处不仅仅在于此。如果您心仪 Lin，却又因为技术栈的原因无法即可使用，没关系，我们也提供了更多的语言版本和框架的后端实现。为什么 Lin 要选择前后端分离的单页面架构呢？

首先，传统的网站开发更多的是采用服务端渲染的方式，需用使用一种模板语言在服务端完成页面渲染：比如 JinJa2、Jade 等。
服务端渲染的好处在于可以比较好的支持 SEO，但作为内部使用的 CMS 管理系统，SEO 并不重要。

但一个不可忽视的事实是，服务器渲染的页面到底是由前端开发者来完成，还是由服务器开发者来完成？其实都不太合适。现在已经没有多少前端开发者是了解这些服务端模板语言的，而服务器开发者本身是不太擅长开发页面的。那还是分开吧，前端用最熟悉的 Vue 写 JS 和 CSS，而服务器只关注自己的 API 即可。

其次，单页面应用程序的体验本身就要好于传统网站。

#### 框架本身已内置了 CMS 常用的功能

Lin 已经内置了 CMS 中最为常见的需求：用户管理、权限管理、日志系统等。开发者只需要集中精力开发自己的 CMS 业务即可

#### Lin CMS 本身也是一套开发规范

Lin CMS 除了内置常见的功能外，还提供了一套开发规范与工具类。换句话说，开发者无需再纠结如何验证参数？如何操作数据库？如何做全局的异常处理？API 的结构如何？前端结构应该如何组织？这些问题 Lin CMS 已经给出了解决方案。当然，如果您不喜欢 Lin 给出的架构，那么自己去实现自己的 CMS 架构也是可以的。但通常情况下，您确实无需再做出架构上的改动，Lin 可以满足绝大多数中小型的 CMS 需求。

举例来说，每个 API 都需要校验客户端传递的参数。但校验的方法有很多种，不同的开发者会有不同的构筑方案。但 Lin 提供了一套验证机制，开发者无需再纠结如何校验参数，只需模仿 Lin 的校验方案去写自己的业务即可。

还是基于这样的一个原则：Lin CMS 只需要开发者关注自己的业务开发，它已经内置了很多机制帮助开发者快速开发自己的业务。

#### 基于插件的扩展

任何优秀的框架都需要考虑到扩展。而 Lin 的扩展支持是通过插件的思想来设计的。当您需要新增一个功能时，您既可以直接在 Lin 的目录下编写代码，也可以将功能以插件的形式封装。比如，您开发了一个文章管理功能，您可以选择以插件的形式来发布，这样其他开发者通过安装您的插件就可以使用这个功能了。毫无疑问，以插件的形式封装功能将最大化代码的可复用性。您甚至可以把自己开发的插件发布，以提供给其他开发者使用。这种机制相当的棒。

#### 前端组件库支持

Lin CMS 还将提供一套类似于 Vue Element 的前端组件库，以方便前端开发者快速开发。相比于 Vue Element 或 iView 等成熟的组件库，Lin 所提供的组件库将针对 Lin CMS 的整体设计风格、交互体验等作出大量的优化，使用 Lin CMS 的组件库将更容易开发出体验更好的 CMS 系统。当然，Lin CMS 本身不限制开发者选用任何的组件库，您完全可以根据自己的喜好/习惯/熟悉度，去选择任意的一个基于 Vue 的组件库，比如前面提到的 Vue Element 和 iView 等。您甚至可以混搭使用。当然，前提是这些组件库是基于 Vue 的。

#### 完善的文档

我们将提供尽可能完善的[文档](https://doc.cms.talelin.com)
来帮助开发者使用 Lin CMS
