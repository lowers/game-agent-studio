<template>
  <div class="text-xs">
    <div v-for="node in tree" :key="node.name">
      <div
        class="flex items-center gap-1.5 px-1.5 py-1 rounded hover:bg-card-hover cursor-pointer transition-colors"
        :style="{ paddingLeft: `${level * 12 + 4}px` }"
        @click="handleClick(node)"
      >
        <span v-if="node.children" class="text-brand-dim/60">
          {{ expanded[node.name] ? '▾' : '▸' }}
        </span>
        <span v-else class="text-brand-dim/30">·</span>
        <span class="text-text-primary truncate">{{ node.name }}</span>
      </div>
      <FileTree
        v-if="node.children && expanded[node.name]"
        :tree="node.children"
        :level="level + 1"
        @select="(n: any) => $emit('select', n)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
interface TreeNode {
  name: string
  path?: string
  children?: TreeNode[]
}

const props = withDefaults(defineProps<{
  tree: TreeNode[]
  level?: number
}>(), {
  level: 0,
})

defineEmits<{
  select: [node: TreeNode]
}>()

const expanded = reactive<Record<string, boolean>>({})

function handleClick(node: TreeNode) {
  if (node.children) {
    expanded[node.name] = !expanded[node.name]
  }
}
</script>
