<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, X, Move, Scan } from "lucide-vue-next";

const props = defineProps<{
  isOpen: boolean;
  svgHtml: string;
  title?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const canvasRef = ref<HTMLElement | null>(null);
const transformRef = ref<HTMLElement | null>(null);

const scale = ref<number>(1);
const pan = ref<{ x: number; y: number }>({ x: 0, y: 0 });
const isDragging = ref<boolean>(false);
const isPinching = ref<boolean>(false);

// Drag tracking
let dragStartPos = { x: 0, y: 0 };
let panStartPos = { x: 0, y: 0 };

// Touch tracking
let initialTouchDist = 0;
let initialTouchScale = 1;
let initialTouchMid = { x: 0, y: 0 };
let initialTouchPan = { x: 0, y: 0 };

// Double tap tracking for touch devices
let lastTapTime = 0;

function clampScale(s: number) {
  return Math.min(Math.max(s, 0.15), 10);
}

function zoomIn() {
  const newScale = clampScale(scale.value * 1.25);
  scale.value = Number(newScale.toFixed(2));
}

function zoomOut() {
  const newScale = clampScale(scale.value * 0.8);
  scale.value = Number(newScale.toFixed(2));
}

function resetZoom() {
  scale.value = 1;
  pan.value = { x: 0, y: 0 };
}

function fitToScreen() {
  if (!canvasRef.value || !transformRef.value) return;
  const svgEl = transformRef.value.querySelector("svg");
  if (!svgEl) return;

  const viewBox = svgEl.getAttribute("viewBox");
  let svgW = 800;
  let svgH = 600;

  if (viewBox) {
    const parts = viewBox
      .trim()
      .split(/[\s,]+/)
      .map(Number);
    if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
      svgW = parts[2];
      svgH = parts[3];
    }
  } else {
    const b = svgEl.getBoundingClientRect();
    if (b.width > 0) svgW = b.width;
    if (b.height > 0) svgH = b.height;
  }

  // Ensure explicit natural dimensions so transforms scale reliably
  svgEl.style.width = `${svgW}px`;
  svgEl.style.height = `${svgH}px`;
  svgEl.style.maxWidth = "none";
  svgEl.style.maxHeight = "none";

  const canvasRect = canvasRef.value.getBoundingClientRect();
  const availableW = Math.max(canvasRect.width - 64, 200);
  const availableH = Math.max(canvasRect.height - 64, 200);

  const scaleRatio = Math.min(availableW / svgW, availableH / svgH, 1.2);
  scale.value = Number(Math.max(scaleRatio, 0.2).toFixed(2));
  pan.value = { x: 0, y: 0 };
}

// Mouse Wheel: zoom relative to cursor position
function handleWheel(e: WheelEvent) {
  e.preventDefault();
  if (!canvasRef.value) return;

  const factor = e.deltaY < 0 ? 1.15 : 0.87;
  const oldScale = scale.value;
  const newScale = clampScale(oldScale * factor);

  const rect = canvasRef.value.getBoundingClientRect();
  const mouseX = e.clientX - (rect.left + rect.width / 2);
  const mouseY = e.clientY - (rect.top + rect.height / 2);

  pan.value.x = mouseX - (mouseX - pan.value.x) * (newScale / oldScale);
  pan.value.y = mouseY - (mouseY - pan.value.y) * (newScale / oldScale);
  scale.value = Number(newScale.toFixed(2));
}

// Mouse Drag / Pan
function handleMouseDown(e: MouseEvent) {
  if (e.button !== 0) return; // Left click only
  isDragging.value = true;
  dragStartPos = { x: e.clientX, y: e.clientY };
  panStartPos = { ...pan.value };
}

function handleMouseMove(e: MouseEvent) {
  if (!isDragging.value) return;
  pan.value.x = panStartPos.x + (e.clientX - dragStartPos.x);
  pan.value.y = panStartPos.y + (e.clientY - dragStartPos.y);
}

function handleMouseUp() {
  isDragging.value = false;
}

// Double click to toggle 2x or reset
function handleDblClick(e: MouseEvent) {
  if (Math.abs(scale.value - 1) < 0.2) {
    if (!canvasRef.value) return;
    const rect = canvasRef.value.getBoundingClientRect();
    const mouseX = e.clientX - (rect.left + rect.width / 2);
    const mouseY = e.clientY - (rect.top + rect.height / 2);
    const newScale = 2;
    pan.value.x = mouseX - (mouseX - pan.value.x) * (newScale / scale.value);
    pan.value.y = mouseY - (mouseY - pan.value.y) * (newScale / scale.value);
    scale.value = newScale;
  } else {
    resetZoom();
  }
}

// Touch Handling (Single finger Pan, Two fingers Pinch-to-zoom)
function handleTouchStart(e: TouchEvent) {
  if (e.touches.length === 1) {
    const now = Date.now();
    if (now - lastTapTime < 300) {
      handleDblClick({
        clientX: e.touches[0].clientX,
        clientY: e.touches[0].clientY,
      } as MouseEvent);
      lastTapTime = 0;
      return;
    }
    lastTapTime = now;

    isDragging.value = true;
    isPinching.value = false;
    dragStartPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    panStartPos = { ...pan.value };
  } else if (e.touches.length >= 2) {
    isDragging.value = false;
    isPinching.value = true;
    const t1 = e.touches[0];
    const t2 = e.touches[1];
    initialTouchDist = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    initialTouchMid = {
      x: (t1.clientX + t2.clientX) / 2,
      y: (t1.clientY + t2.clientY) / 2,
    };
    initialTouchScale = scale.value;
    initialTouchPan = { ...pan.value };
  }
}

function handleTouchMove(e: TouchEvent) {
  e.preventDefault();

  if (isDragging.value && e.touches.length === 1) {
    pan.value.x = panStartPos.x + (e.touches[0].clientX - dragStartPos.x);
    pan.value.y = panStartPos.y + (e.touches[0].clientY - dragStartPos.y);
  } else if (isPinching.value && e.touches.length >= 2) {
    const t1 = e.touches[0];
    const t2 = e.touches[1];
    const curDist = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    const curMid = {
      x: (t1.clientX + t2.clientX) / 2,
      y: (t1.clientY + t2.clientY) / 2,
    };

    const ratio = curDist / (initialTouchDist || 1);
    const newScale = clampScale(initialTouchScale * ratio);

    pan.value.x = initialTouchPan.x + (curMid.x - initialTouchMid.x);
    pan.value.y = initialTouchPan.y + (curMid.y - initialTouchMid.y);
    scale.value = Number(newScale.toFixed(2));
  }
}

function handleTouchEnd(e: TouchEvent) {
  if (e.touches.length === 0) {
    isDragging.value = false;
    isPinching.value = false;
  } else if (e.touches.length === 1) {
    isPinching.value = false;
    isDragging.value = true;
    dragStartPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    panStartPos = { ...pan.value };
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (!props.isOpen) return;
  if (e.key === "Escape") {
    emit("close");
  } else if (e.key === "+" || e.key === "=") {
    zoomIn();
  } else if (e.key === "-" || e.key === "_") {
    zoomOut();
  } else if (e.key === "0") {
    resetZoom();
  }
}

onMounted(() => {
  window.addEventListener("mouseup", handleMouseUp);
  window.addEventListener("mousemove", handleMouseMove);
  window.addEventListener("keydown", handleKeyDown);
});

onBeforeUnmount(() => {
  window.removeEventListener("mouseup", handleMouseUp);
  window.removeEventListener("mousemove", handleMouseMove);
  window.removeEventListener("keydown", handleKeyDown);
});

watch(
  () => props.isOpen,
  async (open) => {
    if (open) {
      await nextTick();
      fitToScreen();
    }
  },
);

watch(
  () => props.svgHtml,
  async () => {
    if (props.isOpen) {
      await nextTick();
      fitToScreen();
    }
  },
);
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[100] flex flex-col justify-between bg-base-300/85 backdrop-blur-xl select-none"
        tabindex="-1"
      >
        <!-- Backdrop click zone -->
        <div class="absolute inset-0 -z-10" @click="emit('close')"></div>

        <!-- Top Header & Floating Controls Toolbar -->
        <div
          class="flex items-center justify-between p-3 sm:px-6 border-b border-base-content/10 bg-base-200/90 backdrop-blur-md shadow-sm z-10"
        >
          <div class="flex items-center gap-2.5">
            <div class="p-1.5 rounded-lg bg-primary/10 text-primary">
              <Maximize2 class="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <div>
              <h3 class="font-bold text-xs sm:text-sm text-base-content leading-tight">
                {{ title || "Mermaid Diagram Preview" }}
              </h3>
              <p class="text-[10px] sm:text-xs text-base-content/60 hidden sm:block">
                Interactive Pan & Zoom View
              </p>
            </div>
          </div>

          <!-- Controls Toolbar -->
          <div class="flex items-center gap-1 sm:gap-2">
            <div class="join bg-base-300/80 p-0.5 rounded-xl border border-base-content/10">
              <button
                @click="zoomOut"
                class="btn btn-xs sm:btn-sm btn-ghost join-item px-2 text-base-content/80 hover:text-base-content"
                title="Zoom Out (-)"
              >
                <ZoomOut class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </button>
              <button
                @click="resetZoom"
                class="btn btn-xs sm:btn-sm btn-ghost join-item px-2 font-mono text-[11px] sm:text-xs font-semibold text-base-content"
                title="Reset to 100% (0)"
              >
                {{ Math.round(scale * 100) }}%
              </button>
              <button
                @click="zoomIn"
                class="btn btn-xs sm:btn-sm btn-ghost join-item px-2 text-base-content/80 hover:text-base-content"
                title="Zoom In (+)"
              >
                <ZoomIn class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </button>
            </div>

            <button
              @click="fitToScreen"
              class="btn btn-xs sm:btn-sm btn-ghost bg-base-300/80 hover:bg-base-300 border border-base-content/10 text-base-content gap-1 px-2.5"
              title="Fit to Screen"
            >
              <Scan class="w-3.5 h-3.5 text-primary" />
              <span class="hidden sm:inline text-xs">Fit</span>
            </button>

            <button
              @click="resetZoom"
              class="btn btn-xs sm:btn-sm btn-ghost bg-base-300/80 hover:bg-base-300 border border-base-content/10 text-base-content gap-1 px-2.5"
              title="Reset View"
            >
              <RotateCcw class="w-3.5 h-3.5" />
              <span class="hidden sm:inline text-xs">Reset</span>
            </button>

            <div class="divider divider-horizontal my-1 mx-0.5"></div>

            <button
              @click="emit('close')"
              class="btn btn-xs sm:btn-sm btn-circle btn-ghost hover:bg-rose-500/20 hover:text-rose-400 text-base-content/70"
              title="Close (ESC)"
            >
              <X class="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          </div>
        </div>

        <!-- Interactive Diagram Canvas Area -->
        <div
          ref="canvasRef"
          class="flex-1 w-full h-full relative overflow-hidden flex items-center justify-center cursor-grab active:cursor-grabbing mermaid-modal-canvas"
          @mousedown="handleMouseDown"
          @wheel.passive="false"
          @wheel="handleWheel"
          @dblclick="handleDblClick"
          @touchstart.passive="false"
          @touchstart="handleTouchStart"
          @touchmove.passive="false"
          @touchmove="handleTouchMove"
          @touchend="handleTouchEnd"
        >
          <!-- Transformed SVG wrapper -->
          <div
            ref="transformRef"
            class="mermaid-modal-transform select-none flex items-center justify-center p-8 pointer-events-none"
            :style="{
              transform: `translate3d(${pan.x}px, ${pan.y}px, 0) scale(${scale})`,
              transformOrigin: 'center center',
              transition: isDragging || isPinching ? 'none' : 'transform 0.08s ease-out',
            }"
            v-html="svgHtml"
          ></div>
        </div>

        <!-- Bottom Gesture Hint & Status -->
        <div
          class="p-2.5 sm:p-3 border-t border-base-content/10 bg-base-200/90 backdrop-blur-md flex items-center justify-between text-xs text-base-content/60 px-4 sm:px-6 z-10"
        >
          <div class="flex items-center gap-2">
            <Move class="w-3.5 h-3.5 text-primary animate-pulse" />
            <span class="text-[11px] sm:text-xs"
              >Drag to pan • Scroll or pinch to zoom • Double-click to toggle zoom</span
            >
          </div>
          <div class="hidden sm:flex items-center gap-3 font-mono text-[11px] text-base-content/50">
            <span>Scale: {{ Math.round(scale * 100) }}%</span>
            <span>X: {{ Math.round(pan.x) }}px</span>
            <span>Y: {{ Math.round(pan.y) }}px</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
