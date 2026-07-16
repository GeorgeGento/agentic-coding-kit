# Ionic Vue Reference

## Table of Contents
1. [Project Setup](#project-setup)
2. [Routing](#routing)
3. [Ionic Lifecycle Hooks](#ionic-lifecycle-hooks)
4. [State Management with Pinia](#state-management-with-pinia)
5. [Composition API Patterns](#composition-api-patterns)
6. [Form Handling](#form-handling)
7. [Component Patterns](#component-patterns)
8. [Testing](#testing)

---

## Project Setup

```bash
ionic start myApp tabs --type=vue
cd myApp
ionic serve
```

### Key Dependencies

```json
{
  "@ionic/vue": "^8.x",
  "@ionic/vue-router": "^8.x",
  "vue": "^3.x",
  "vue-router": "^4.x",
  "pinia": "^2.x",
  "ionicons": "^7.x"
}
```

### App Entry Point

```typescript
// main.ts
import { createApp } from 'vue';
import { IonicVue } from '@ionic/vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';

/* Core CSS */
import '@ionic/vue/css/core.css';
import '@ionic/vue/css/normalize.css';
import '@ionic/vue/css/structure.css';
import '@ionic/vue/css/typography.css';

/* Optional utilities */
import '@ionic/vue/css/padding.css';
import '@ionic/vue/css/float-elements.css';
import '@ionic/vue/css/text-alignment.css';
import '@ionic/vue/css/text-transformation.css';
import '@ionic/vue/css/flex-utils.css';
import '@ionic/vue/css/display.css';

/* Dark mode */
import '@ionic/vue/css/palettes/dark.system.css';

/* Theme */
import './theme/variables.css';

const pinia = createPinia();
const app = createApp(App);

app.use(IonicVue);
app.use(pinia);
app.use(router);

router.isReady().then(() => {
  app.mount('#app');
});
```

```vue
<!-- App.vue -->
<template>
  <ion-app>
    <ion-router-outlet />
  </ion-app>
</template>

<script setup lang="ts">
import { IonApp, IonRouterOutlet } from '@ionic/vue';
</script>
```

## Routing

### Route Configuration

```typescript
// router/index.ts
import { createRouter, createWebHistory } from '@ionic/vue-router';
import type { RouteRecordRaw } from 'vue-router';
import TabsPage from '../pages/TabsPage.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/tabs/home',
  },
  {
    path: '/login',
    component: () => import('../pages/LoginPage.vue'),
  },
  {
    path: '/tabs/',
    component: TabsPage,
    children: [
      {
        path: '',
        redirect: '/tabs/home',
      },
      {
        path: 'home',
        component: () => import('../pages/HomePage.vue'),
      },
      {
        path: 'search',
        component: () => import('../pages/SearchPage.vue'),
      },
      {
        path: 'profile',
        component: () => import('../pages/ProfilePage.vue'),
      },
    ],
  },
  {
    path: '/detail/:id',
    component: () => import('../pages/DetailPage.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
```

### Tabs Layout

```vue
<!-- pages/TabsPage.vue -->
<template>
  <ion-page>
    <ion-tabs>
      <ion-router-outlet />
      <ion-tab-bar slot="bottom">
        <ion-tab-button tab="home" href="/tabs/home">
          <ion-icon :icon="home" />
          <ion-label>Home</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="search" href="/tabs/search">
          <ion-icon :icon="search" />
          <ion-label>Search</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="profile" href="/tabs/profile">
          <ion-icon :icon="person" />
          <ion-label>Profile</ion-label>
        </ion-tab-button>
      </ion-tab-bar>
    </ion-tabs>
  </ion-page>
</template>

<script setup lang="ts">
import {
  IonPage, IonTabs, IonTabBar, IonTabButton,
  IonIcon, IonLabel, IonRouterOutlet,
} from '@ionic/vue';
import { home, search, person } from 'ionicons/icons';
</script>
```

### Programmatic Navigation

```vue
<script setup lang="ts">
import { useIonRouter } from '@ionic/vue';

const router = useIonRouter();

const goToDetail = (id: string) => {
  router.push(`/detail/${id}`);
};

const goBack = () => {
  if (router.canGoBack()) {
    router.back();
  }
};
</script>
```

### Navigation Guards

```typescript
// router/index.ts
import { useAuthStore } from '../stores/auth';

router.beforeEach((to) => {
  const auth = useAuthStore();

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login';
  }
});

// In route definition:
{
  path: 'profile',
  component: () => import('../pages/ProfilePage.vue'),
  meta: { requiresAuth: true },
}
```

## Ionic Lifecycle Hooks

Vue's `onMounted`/`onUnmounted` only fire once because Ionic keeps pages in the DOM. Use Ionic-specific hooks:

```vue
<script setup lang="ts">
import {
  onIonViewWillEnter,
  onIonViewDidEnter,
  onIonViewWillLeave,
  onIonViewDidLeave,
} from '@ionic/vue';

// Fires before the page animates in — load data here
onIonViewWillEnter(() => {
  fetchData();
});

// Fires after the page is visible — start animations, track analytics
onIonViewDidEnter(() => {
  analyticsTrack('home_viewed');
});

// Fires before leaving — save drafts, pause media
onIonViewWillLeave(() => {
  saveDraft();
});

// Fires after the page has left — cleanup
onIonViewDidLeave(() => {
  clearTimers();
});
</script>
```

These hooks only fire on page-level components (direct children of `ion-router-outlet`). Pass data to child components via props or provide/inject.

## State Management with Pinia

### Store Definition (Setup Syntax)

```typescript
// stores/items.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from '../services/api';

export const useItemsStore = defineStore('items', () => {
  // State
  const items = ref<Item[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const searchTerm = ref('');

  // Getters (computed)
  const filteredItems = computed(() =>
    items.value.filter((item) =>
      item.name.toLowerCase().includes(searchTerm.value.toLowerCase())
    )
  );

  const itemCount = computed(() => filteredItems.value.length);

  // Actions
  async function fetchItems() {
    isLoading.value = true;
    error.value = null;
    try {
      items.value = await api.getItems();
    } catch (e) {
      error.value = (e as Error).message;
    } finally {
      isLoading.value = false;
    }
  }

  async function addItem(item: Partial<Item>) {
    const newItem = await api.createItem(item);
    items.value.push(newItem);
  }

  async function deleteItem(id: string) {
    await api.deleteItem(id);
    items.value = items.value.filter((i) => i.id !== id);
  }

  return {
    items,
    isLoading,
    error,
    searchTerm,
    filteredItems,
    itemCount,
    fetchItems,
    addItem,
    deleteItem,
  };
});
```

### Auth Store with Capacitor Preferences

```typescript
// stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Preferences } from '@capacitor/preferences';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);

  const isAuthenticated = computed(() => token.value !== null);

  async function login(credentials: Credentials) {
    const response = await api.login(credentials);
    user.value = response.user;
    token.value = response.token;
    await Preferences.set({ key: 'auth_token', value: response.token });
  }

  async function logout() {
    user.value = null;
    token.value = null;
    await Preferences.remove({ key: 'auth_token' });
  }

  async function restoreSession() {
    const { value } = await Preferences.get({ key: 'auth_token' });
    if (value) {
      token.value = value;
      user.value = await api.getProfile(value);
    }
  }

  return { user, token, isAuthenticated, login, logout, restoreSession };
});
```

### Using Stores in Components

```vue
<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Items ({{ store.itemCount }})</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content>
      <ion-searchbar
        :value="store.searchTerm"
        @ionInput="store.searchTerm = $event.detail.value ?? ''"
        placeholder="Search items..."
      />

      <ion-refresher slot="fixed" @ionRefresh="handleRefresh($event)">
        <ion-refresher-content />
      </ion-refresher>

      <ion-list v-if="!store.isLoading">
        <ion-item-sliding v-for="item in store.filteredItems" :key="item.id">
          <ion-item @click="goToDetail(item.id)">
            <ion-label>
              <h2>{{ item.name }}</h2>
              <p>{{ item.description }}</p>
            </ion-label>
          </ion-item>
          <ion-item-options side="end">
            <ion-item-option color="danger" @click="store.deleteItem(item.id)">
              Delete
            </ion-item-option>
          </ion-item-options>
        </ion-item-sliding>
      </ion-list>

      <!-- Skeleton loading -->
      <ion-list v-else>
        <ion-item v-for="i in 5" :key="i">
          <ion-label>
            <h2><ion-skeleton-text :animated="true" style="width: 60%" /></h2>
            <p><ion-skeleton-text :animated="true" style="width: 80%" /></p>
          </ion-label>
        </ion-item>
      </ion-list>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { onIonViewWillEnter } from '@ionic/vue';
import { useIonRouter } from '@ionic/vue';
import { useItemsStore } from '../stores/items';

const store = useItemsStore();
const router = useIonRouter();

onIonViewWillEnter(() => {
  store.fetchItems();
});

const handleRefresh = async (event: CustomEvent) => {
  await store.fetchItems();
  (event.target as HTMLIonRefresherElement).complete();
};

const goToDetail = (id: string) => {
  router.push(`/detail/${id}`);
};
</script>
```

## Composition API Patterns

### Composables for Reusable Logic

```typescript
// composables/useCamera.ts
import { ref } from 'vue';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { useIonToast } from '@ionic/vue';

export function useCamera() {
  const photo = ref<string | null>(null);
  const { present: presentToast } = useIonToast();

  async function takePhoto() {
    try {
      const image = await Camera.getPhoto({
        quality: 90,
        resultType: CameraResultType.Uri,
        source: CameraSource.Prompt,
      });
      photo.value = image.webPath ?? null;
      return image.webPath;
    } catch (error) {
      if ((error as Error).message !== 'User cancelled photos app') {
        presentToast({ message: 'Camera error', color: 'danger', duration: 2000 });
      }
      return null;
    }
  }

  return { photo, takePhoto };
}
```

```typescript
// composables/useNetwork.ts
import { ref, onMounted, onUnmounted } from 'vue';
import { Network } from '@capacitor/network';
import type { PluginListenerHandle } from '@capacitor/core';

export function useNetwork() {
  const isOnline = ref(true);
  const connectionType = ref('unknown');
  let listener: PluginListenerHandle | null = null;

  onMounted(async () => {
    const status = await Network.getStatus();
    isOnline.value = status.connected;
    connectionType.value = status.connectionType;

    listener = await Network.addListener('networkStatusChange', (status) => {
      isOnline.value = status.connected;
      connectionType.value = status.connectionType;
    });
  });

  onUnmounted(() => {
    listener?.remove();
  });

  return { isOnline, connectionType };
}
```

### Provide/Inject for Scoped State

```typescript
// Provide theme context
// App.vue
import { provide, ref } from 'vue';

const isDark = ref(false);
const toggleDark = () => {
  isDark.value = !isDark.value;
  document.documentElement.classList.toggle('ion-palette-dark');
};

provide('theme', { isDark, toggleDark });

// Consume in any child
// SettingsPage.vue
const { isDark, toggleDark } = inject('theme')!;
```

## Form Handling

### VeeValidate with Ionic

```vue
<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Contact</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <form @submit.prevent="onSubmit">
        <ion-list>
          <ion-item>
            <ion-input
              v-model="name"
              label="Name"
              label-placement="stacked"
              fill="outline"
              :class="{ 'ion-invalid ion-touched': errors.name }"
              :error-text="errors.name"
            />
          </ion-item>

          <ion-item>
            <ion-input
              v-model="email"
              label="Email"
              label-placement="stacked"
              fill="outline"
              type="email"
              :class="{ 'ion-invalid ion-touched': errors.email }"
              :error-text="errors.email"
            />
          </ion-item>

          <ion-item>
            <ion-textarea
              v-model="message"
              label="Message"
              label-placement="stacked"
              fill="outline"
              :auto-grow="true"
              :rows="4"
            />
          </ion-item>
        </ion-list>

        <ion-button expand="block" type="submit" :disabled="!meta.valid">
          Send
        </ion-button>
      </form>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { useForm, useField } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

const schema = toTypedSchema(
  z.object({
    name: z.string().min(2, 'Name must be at least 2 characters'),
    email: z.string().email('Invalid email address'),
    message: z.string().optional(),
  })
);

const { handleSubmit, errors, meta } = useForm({ validationSchema: schema });
const { value: name } = useField('name');
const { value: email } = useField('email');
const { value: message } = useField('message');

const onSubmit = handleSubmit(async (values) => {
  console.log(values);
});
</script>
```

### Simple v-model Forms

For simpler forms, Vue's built-in v-model works well with Ionic components:

```vue
<script setup lang="ts">
import { ref } from 'vue';

const form = ref({
  name: '',
  category: '',
  notifications: true,
});

const submit = () => {
  console.log(form.value);
};
</script>

<template>
  <ion-list>
    <ion-item>
      <ion-input
        v-model="form.name"
        label="Name"
        label-placement="stacked"
        fill="outline"
      />
    </ion-item>
    <ion-item>
      <ion-select
        v-model="form.category"
        label="Category"
        label-placement="stacked"
      >
        <ion-select-option value="a">Option A</ion-select-option>
        <ion-select-option value="b">Option B</ion-select-option>
      </ion-select>
    </ion-item>
    <ion-item>
      <ion-toggle v-model="form.notifications">Notifications</ion-toggle>
    </ion-item>
  </ion-list>
  <ion-button expand="block" @click="submit">Submit</ion-button>
</template>
```

## Component Patterns

### Reusable List Component

```vue
<!-- components/ItemList.vue -->
<template>
  <ion-list>
    <ion-item-sliding v-for="item in items" :key="item.id">
      <ion-item button @click="$emit('select', item)">
        <ion-thumbnail v-if="item.image" slot="start">
          <ion-img :src="item.image" />
        </ion-thumbnail>
        <ion-label>
          <h2>{{ item.title }}</h2>
          <p v-if="item.subtitle">{{ item.subtitle }}</p>
        </ion-label>
        <ion-icon :icon="chevronForward" slot="end" color="medium" />
      </ion-item>
      <ion-item-options v-if="deletable" side="end">
        <ion-item-option color="danger" @click="$emit('delete', item.id)">
          <ion-icon :icon="trash" slot="icon-only" />
        </ion-item-option>
      </ion-item-options>
    </ion-item-sliding>
  </ion-list>
</template>

<script setup lang="ts">
import { chevronForward, trash } from 'ionicons/icons';

interface ListItem {
  id: string;
  title: string;
  subtitle?: string;
  image?: string;
}

defineProps<{
  items: ListItem[];
  deletable?: boolean;
}>();

defineEmits<{
  select: [item: ListItem];
  delete: [id: string];
}>();
</script>
```

### Modal Pattern

```vue
<!-- components/CreateItemModal.vue -->
<template>
  <ion-header>
    <ion-toolbar>
      <ion-buttons slot="start">
        <ion-button @click="dismiss()">Cancel</ion-button>
      </ion-buttons>
      <ion-title>New Item</ion-title>
      <ion-buttons slot="end">
        <ion-button :strong="true" @click="save()">Save</ion-button>
      </ion-buttons>
    </ion-toolbar>
  </ion-header>
  <ion-content class="ion-padding">
    <ion-input
      v-model="name"
      label="Name"
      label-placement="stacked"
      fill="outline"
    />
  </ion-content>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { modalController } from '@ionic/vue';

const name = ref('');

const dismiss = () => modalController.dismiss(null, 'cancel');
const save = () => modalController.dismiss({ name: name.value }, 'confirm');
</script>

<!-- Usage in parent -->
<script setup lang="ts">
import { modalController } from '@ionic/vue';
import CreateItemModal from '../components/CreateItemModal.vue';

const openModal = async () => {
  const modal = await modalController.create({
    component: CreateItemModal,
    breakpoints: [0, 0.5, 1],
    initialBreakpoint: 0.5,
  });

  await modal.present();
  const { data, role } = await modal.onDidDismiss();

  if (role === 'confirm' && data) {
    store.addItem(data);
  }
};
</script>
```

## Testing

### Component Testing with Vitest

```typescript
import { mount } from '@vue/test-utils';
import { IonicVue } from '@ionic/vue';
import { createTestingPinia } from '@pinia/testing';
import HomePage from '../pages/HomePage.vue';

describe('HomePage', () => {
  it('renders items', async () => {
    const wrapper = mount(HomePage, {
      global: {
        plugins: [
          IonicVue,
          createTestingPinia({
            initialState: {
              items: {
                items: [
                  { id: '1', name: 'Test Item', description: 'Test' },
                ],
                isLoading: false,
              },
            },
          }),
        ],
      },
    });

    expect(wrapper.text()).toContain('Test Item');
  });
});
```

### Composable Testing

```typescript
import { setActivePinia, createPinia } from 'pinia';
import { useItemsStore } from '../stores/items';

describe('useItemsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('filters items by search term', () => {
    const store = useItemsStore();
    store.items = [
      { id: '1', name: 'Apple' },
      { id: '2', name: 'Banana' },
    ];
    store.searchTerm = 'app';

    expect(store.filteredItems).toHaveLength(1);
    expect(store.filteredItems[0].name).toBe('Apple');
  });
});
```
