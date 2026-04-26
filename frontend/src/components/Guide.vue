<script setup>
import { 
  Sparkles, 
  AlertTriangle, 
  Layers,
  ShieldCheck,
  Workflow,
  Database,
  CheckCircle,
  Scale,
  Scan,
  UserCircle,
  MessageSquare,
  BarChart3,
  RefreshCw
} from 'lucide-vue-next'
import Page01 from './guide/Page01.vue'
import Page02 from './guide/Page02.vue'
import Page03 from './guide/Page03.vue'
import Page04 from './guide/Page04.vue'
import Page05 from './guide/Page05.vue'
import Page06 from './guide/Page06.vue'
import Page07 from './guide/Page07.vue'
import Page08 from './guide/Page08.vue'
import Page09 from './guide/Page09.vue'
import Page10 from './guide/Page10.vue'
import Page11 from './guide/Page11.vue'
import Page12 from './guide/Page12.vue'
import Page13 from './guide/Page13.vue'

const props = defineProps({
  currentSlide: {
    type: Number,
    default: 0
  },
  isPrinting: {
    type: Boolean,
    default: false
  }
})

const slides = [
  {
    title: "Introduction to HiringAgent",
    subtitle: "AI-Driven Recruitment Pipeline",
    content: "HiringAgent is an advanced platform that orchestrates specialized AI agents to streamline the entire recruitment lifecycle. From resume structuring to deep technical evaluation and background analysis, it provides a comprehensive, objective, and efficient way to identify top talent.",
    icon: Sparkles,
    color: "var(--accent)",
    component: Page01
  },
  {
    title: "Problem Statement",
    subtitle: "The Hiring Bottleneck",
    content: "Modern recruitment faces critical challenges: Information Overload from massive applicant pools, Hidden Potential masked by rigid keyword filters, and Unconscious Bias in initial screenings. HiringAgent solves these by providing deep, multi-perspective evaluation and automated validation of candidate claims.",
    icon: AlertTriangle,
    color: "var(--err)",
    component: Page02
  },
  {
    title: "System Architecture",
    subtitle: "Bottom-to-Top Overview",
    content: "Built on a robust stack: (1) Foundation: FerretDB/PostgreSQL with CosmosSearch for vector retrieval. (2) Agents: Specialized LLM units for OCR, structured parsing, and competitive scoring. (3) Orchestration: LangGraph-powered workflows and async pipelines. (4) Interface: FastAPI back-end with a modern Vue 3 responsive dashboard.",
    icon: Layers,
    color: "var(--ok)",
    component: Page03
  },
  {
    title: "Safety & Integrity",
    subtitle: "Role-Aware Guardrails",
    content: "Security is built-in. Every candidate interaction is scrutinized by a real-time safety classifier to detect prompt injection, roleplay attempts, and off-topic behavior. This ensures the platform remains professional and focused on its core mission while protecting system integrity.",
    icon: ShieldCheck,
    color: "var(--accent)",
    component: Page04
  },
  {
    title: "AI Orchestration",
    subtitle: "LangChain & Tool Harness",
    content: "Our sophisticated tool harness ensures that AI capabilities are both powerful and secure. By dynamically injecting tools based on user roles and utilizing LangGraph for stateful task isolation, we maintain strict control over LLM sessions while providing rich, contextual automation.",
    icon: Workflow,
    color: "var(--ok)",
    component: Page05
  },
  {
    title: "Data & Vector",
    subtitle: "FerretDB & Semantic Matching",
    content: "We use FerretDB as a transparent MongoDB-compatible layer over PostgreSQL, providing a flexible document API with the reliability of a relational backend. Integrated vector search powered by OpenAI embeddings enables lightning-fast semantic matching between candidates and job requirements.",
    icon: Database,
    color: "var(--accent)",
    component: Page06
  },
  {
    title: "Quality & CI/CD",
    subtitle: "Reproducible Engineering",
    content: "Stability is guaranteed through a rigorous testing pipeline and reproducible environments. We leverage Nix Flakes for hermetic builds, Pytest for comprehensive unit and integration testing, and GitHub Actions for automated validation of every change across the entire system.",
    icon: CheckCircle,
    color: "var(--ok)",
    component: Page07
  },
  {
    title: "Competitive Evaluation",
    subtitle: "Competing Experts Panel",
    content: "We move beyond simple LLM summaries by using a 4-agent panel of Advocates, Critics, and Logic Auditors. This competitive setup, overseen by a meritocratic Judge, ensures deep technical evaluation while eliminating the 'regression to the mean' common in basic AI models.",
    icon: Scale,
    color: "var(--accent)",
    component: Page08
  },
  {
    title: "Data Arrangement",
    subtitle: "Structural Extraction & Sanitization",
    content: "We transform raw resume files into high-density structured profiles. By isolating the OCR and parsing phase from the analysis, and applying real-time injection sanitization, we ensure candidate data is both safe to process and effortless for recruiters to review.",
    icon: Scan,
    color: "var(--ok)",
    component: Page09
  },
  {
    title: "Access Control",
    subtitle: "Accounts & Role-Based Hardening",
    content: "Security starts at the entry point. With strict RBAC separation between recruiters and candidates, dedicated API endpoints, and identity-aware LLM sessions, we ensure that every interaction is authenticated and every AI action is properly scoped.",
    icon: UserCircle,
    color: "var(--accent)",
    component: Page10
  },
  {
    title: "AI Assistant",
    subtitle: "Context-Aware Chat Bot",
    content: "Our persistent AI assistant provides role-specific support by automatically capturing page context and user selections. It operates as a secure proxy, executing tools on your behalf while maintaining strict role-based data isolation and returning interactive entity cards.",
    icon: MessageSquare,
    color: "var(--ok)",
    component: Page11
  },
  {
    title: "Resource Auditing",
    subtitle: "Token Usage & Cost Analysis",
    content: "We provide granular visibility into AI consumption. By tracking token usage per user and per tool, the platform allows for precise cost management, behavior auditing, and the proactive detection of anomalies in automated workflows.",
    icon: BarChart3,
    color: "var(--accent)",
    component: Page12
  },
  {
    title: "Candidate Experience",
    subtitle: "Centralized Resume Management",
    content: "Efficiency for the applicant. Candidates upload their resume and connect external profiles (GitHub/Scholar) only once. For every specific job, a brief 200-word statement is all that's needed to trigger a targeted, high-fidelity match analysis.",
    icon: RefreshCw,
    color: "var(--ok)",
    component: Page13
  }
]
</script>

<template>
  <div :class="['guide-full-page', { 'is-printing-active': isPrinting }]">
    <!-- Normal Interactive Mode -->
    <template v-if="!isPrinting">
      <template v-for="(slide, index) in slides" :key="index">
        <div 
          class="slide-wrapper"
          v-if="currentSlide === index"
        >
          <component :is="slide.component" :slide="slide" />
        </div>
      </template>
    </template>

    <!-- Print Mode (Render all slides) -->
    <template v-else>
      <div v-for="(slide, index) in slides" :key="'print-' + index" class="print-page">
        <component :is="slide.component" :slide="slide" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.guide-full-page {
  flex: 1;
  display: flex;
  background: radial-gradient(circle at 50% 50%, var(--glass), transparent);
  overflow: hidden;
}

.guide-full-page.is-printing-active {
  display: block;
  overflow: visible;
  height: auto;
  background: var(--bg);
}

.slide-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  animation: slideFade 0.5s ease-out;
}

.print-page {
  width: 1920px;
  height: 1080px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem; /* Reduced from 8rem */
  page-break-after: always;
  background: var(--bg);
  color: var(--text);
  position: relative;
  overflow: hidden;
  /* Force background colors */
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* Enlarge content container specifically for print */
.is-printing-active :deep(.slide-content-container) {
  max-width: 1600px !important;
}

/* Disable 3D transforms for high-fidelity PDF output (prevents raster blur) */
.is-printing-active :deep(.visual-stack),
.is-printing-active :deep(.demo-dashboard),
.is-printing-active :deep(.slide-demo-slice),
.is-printing-active :deep(.pain-points-visual),
.is-printing-active :deep(.harness-visual),
.is-printing-active :deep(.db-visual),
.is-printing-active :deep(.qa-visual),
.is-printing-active :deep(.experts-visual),
.is-printing-active :deep(.guardrail-visual) {
  transform: none !important;
  perspective: none !important;
}

/* Ensure background patterns and gradients are visible in print */
@media print {
  @page {
    size: 1920px 1080px;
    margin: 0;
  }
  
  .print-page {
    border: none;
    background: var(--bg) !important;
  }
}

@keyframes slideFade {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
