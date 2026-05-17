# MCP使用教程
```
以playwright为例
Playwright 是微软开源的现代浏览器自动化框架，
可通过编程方式模拟真实用户在浏览器中的操作，
广泛用于端到端测试（E2E）、网页自动化和数据采集。
```

## 1. 在项目目录里初始化项目

建议在项目目录底下先创建一个独立文件夹保存本地MCP，避免把文件散落到用户根目录。

### 1.1 创建目录并进入

```powershell
mkdir ~\Business_Analytics_Agent\MCP（填写实际的项目目录）
cd ~\Business_Analytics_Agent\MCP
```

### 1.2 初始化 npm 项目

```powershell
npm init -y
```

这一步会生成 `package.json`，用于管理项目依赖与脚本。

### 1.3 安装 Playwright 测试包

```powershell
npm install @playwright/test
```

这一步才是真正安装 Playwright 相关依赖。

### 1.4 下载浏览器

```powershell
npx playwright install
```

这会下载 Playwright 所需的浏览器，包括：

- Chromium
- Firefox
- WebKit

---

## 2. 安装 MCP 包

进入项目目录后，安装 `@playwright/mcp`：

```powershell
cd ~\Business_Analytics_Agent\MCP
npm i -D @playwright/mcp
```

安装完成后，检查包内容：

```powershell
dir C:\playwright-test\node_modules\@playwright\mcp
```

你应该能看到类似这些文件：

- `cli.js`
- `index.js`
- `package.json`
- `README.md`

例如你当前目录结构中已经确认存在：

```text
C:\playwright-test\node_modules\@playwright\mcp\cli.js
```

这说明入口文件已经找到了。

---

## 3. MCP 的配置方式
如图，在配置栏书写下面的内容，点击连接：

![MCP](Images/MCP0.png)



## FAQ

Q：远程MCP如何配置？

A：如下图，按照远程服务器的要求进行填写
![MCP](Images/MCP3.png)