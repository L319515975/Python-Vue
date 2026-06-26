<!--
  根组件 App.vue —— 整个应用的最顶层组件。

  作用：
  1. 定义全局 CSS 样式（重置浏览器默认样式）
  2. 使用 <router-view> 渲染当前路由对应的页面组件

  知识点（Vue 3 组件结构）：
  - <template>：HTML 模板，定义组件的 DOM 结构
  - <script setup>：Vue 3 的组合式 API 语法糖，简化代码编写
  - <style>：CSS 样式，scoped 表示样式只作用于当前组件

  <router-view> 是 Vue Router 提供的组件，
  它会根据当前 URL 路径，动态渲染对应的页面组件。
  例如：
  - URL=/login → 渲染 Login.vue
  - URL=/admin → 渲染 Layout.vue + Dashboard.vue
-->
<template>
  <div id="app">
    <!-- 路由出口：根据 URL 动态渲染对应的页面组件 -->
    <router-view />
  </div>
</template>

<script setup>
// Vue 3 组合式 API 语法糖（<script setup>）
// 这里不需要导出任何东西，所有顶层变量/函数都自动暴露给模板使用
// 本组件逻辑简单，不需要额外的代码
</script>

<style>
/*
 * 全局 CSS 重置 —— 消除浏览器默认样式的差异。
 * 不使用 scoped，这样这些样式会应用到整个应用。
 */
* {
  margin: 0;        /* 清除外边距 */
  padding: 0;       /* 清除内边距 */
  box-sizing: border-box;  /* 让 width/height 包含 padding 和 border */
}

html, body, #app {
  height: 100%;     /* 让整个页面占满视口高度 */
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;  /* 设置中英文字体 */
}
</style>