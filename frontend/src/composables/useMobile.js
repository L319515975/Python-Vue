/**
 * 移动端检测 Composable —— 响应式地检测当前视口是否为移动端宽度。
 *
 * 作用：在不同组件中复用"是否是移动端"的判断逻辑。
 *
 * 知识点（Vue 3 Composable 模式）：
 * - Composable 是一个普通函数，返回响应式数据和方法
 * - 命名约定以 "use" 开头（如 useMobile、useUser）
 * - 内部使用 Vue 的生命周期钩子（onMounted/onUnmounted）管理副作用
 * - 比 mixin 更灵活，可以传参数、返回多个值
 *
 * 使用方式：
 * const { isMobile } = useMobile()         // 默认断点 768px
 * const { isMobile } = useMobile(1024)      // 自定义断点 1024px
 */
import { ref, onMounted, onUnmounted } from 'vue'

export function useMobile(breakpoint = 768) {
  // 响应式变量：当前视口宽度是否 <= 断点
  const isMobile = ref(window.innerWidth <= breakpoint)

  // 窗口大小变化时更新 isMobile
  function onResize() {
    isMobile.value = window.innerWidth <= breakpoint
  }

  // 组件挂载时监听窗口大小变化事件
  onMounted(() => window.addEventListener('resize', onResize))
  // 组件卸载时移除监听（防止内存泄漏）
  onUnmounted(() => window.removeEventListener('resize', onResize))

  return { isMobile }
}