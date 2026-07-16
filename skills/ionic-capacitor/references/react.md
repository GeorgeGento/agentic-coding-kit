# Ionic React Reference

## Table of Contents
1. [Project Setup](#project-setup)
2. [Routing](#routing)
3. [Ionic Lifecycle Hooks](#ionic-lifecycle-hooks)
4. [State Management](#state-management)
5. [Form Handling](#form-handling)
6. [Component Patterns](#component-patterns)
7. [Testing](#testing)

---

## Project Setup

```bash
ionic start myApp tabs --type=react
cd myApp
ionic serve
```

### Key Dependencies

```json
{
  "@ionic/react": "^8.x",
  "@ionic/react-router": "^8.x",
  "react-router-dom": "^6.x",
  "ionicons": "^7.x"
}
```

### App Entry Point

```tsx
// App.tsx
import { IonApp, IonRouterOutlet, setupIonicReact } from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';

/* Core CSS required for Ionic components */
import '@ionic/react/css/core.css';
import '@ionic/react/css/normalize.css';
import '@ionic/react/css/structure.css';
import '@ionic/react/css/typography.css';

/* Optional CSS utilities */
import '@ionic/react/css/padding.css';
import '@ionic/react/css/float-elements.css';
import '@ionic/react/css/text-alignment.css';
import '@ionic/react/css/text-transformation.css';
import '@ionic/react/css/flex-utils.css';
import '@ionic/react/css/display.css';

/* Dark mode */
import '@ionic/react/css/palettes/dark.system.css';

/* Theme */
import './theme/variables.css';

setupIonicReact();  // Initialize Ionic React

const App: React.FC = () => (
  <IonApp>
    <IonReactRouter>
      <IonRouterOutlet>
        {/* Routes */}
      </IonRouterOutlet>
    </IonReactRouter>
  </IonApp>
);
```

## Routing

Ionic React uses `@ionic/react-router` which wraps React Router v5/v6 with page transition animations.

### Tab-Based Routing

```tsx
import { IonTabs, IonTabBar, IonTabButton, IonIcon, IonLabel,
         IonRouterOutlet } from '@ionic/react';
import { Route, Redirect } from 'react-router-dom';
import { home, search, person } from 'ionicons/icons';

const AppTabs: React.FC = () => (
  <IonTabs>
    <IonRouterOutlet>
      <Route exact path="/home" component={HomePage} />
      <Route exact path="/search" component={SearchPage} />
      <Route exact path="/profile" component={ProfilePage} />
      <Route exact path="/home/:id" component={DetailPage} />
      <Route exact path="/">
        <Redirect to="/home" />
      </Route>
    </IonRouterOutlet>
    <IonTabBar slot="bottom">
      <IonTabButton tab="home" href="/home">
        <IonIcon icon={home} />
        <IonLabel>Home</IonLabel>
      </IonTabButton>
      <IonTabButton tab="search" href="/search">
        <IonIcon icon={search} />
        <IonLabel>Search</IonLabel>
      </IonTabButton>
      <IonTabButton tab="profile" href="/profile">
        <IonIcon icon={person} />
        <IonLabel>Profile</IonLabel>
      </IonTabButton>
    </IonTabBar>
  </IonTabs>
);
```

### Programmatic Navigation

```tsx
import { useIonRouter } from '@ionic/react';

const MyComponent: React.FC = () => {
  const router = useIonRouter();

  const goToDetail = (id: string) => {
    router.push(`/detail/${id}`, 'forward', 'push');
    // direction: 'forward' | 'back' | 'root' | 'none'
    // animation: 'push' | 'pop' | 'replace'
  };

  const goBack = () => {
    if (router.canGoBack()) {
      router.goBack();
    }
  };
};
```

### Route Guards

```tsx
import { Route, Redirect } from 'react-router-dom';

const ProtectedRoute: React.FC<{ component: React.FC; path: string }> = ({
  component: Component,
  path,
  ...rest
}) => {
  const { isAuthenticated } = useAuth();

  return (
    <Route
      path={path}
      {...rest}
      render={(props) =>
        isAuthenticated ? <Component {...props} /> : <Redirect to="/login" />
      }
    />
  );
};
```

## Ionic Lifecycle Hooks

Ionic keeps pages mounted in the DOM for smooth back-navigation. Standard React `useEffect` fires only on first mount. Use Ionic lifecycle hooks for view-enter/leave logic:

```tsx
import {
  useIonViewWillEnter,
  useIonViewDidEnter,
  useIonViewWillLeave,
  useIonViewDidLeave,
} from '@ionic/react';

const MyPage: React.FC = () => {
  // Fires before page transition animation starts
  useIonViewWillEnter(() => {
    fetchData();  // Pre-load data for perceived speed
  });

  // Fires after page is fully visible
  useIonViewDidEnter(() => {
    startAnimation();  // Expensive operations after visible
    analyticsTrackView();
  });

  // Fires before leaving — cleanup
  useIonViewWillLeave(() => {
    pauseVideo();
    saveFormDraft();
  });

  // Fires after page is no longer visible
  useIonViewDidLeave(() => {
    clearIntervals();
  });

  // You can also pass dependencies (like useEffect):
  useIonViewDidEnter(() => {
    fetchItem(itemId);
  }, [itemId]);

  return <IonPage>{/* ... */}</IonPage>;
};
```

These hooks only fire on direct children of `IonRouterOutlet` (page components). Child components should receive data via props or context.

## State Management

### Local State — useState/useReducer

For component-local state, standard React hooks work fine:

```tsx
const [items, setItems] = useState<Item[]>([]);
const [isLoading, setIsLoading] = useState(false);
```

### Server State — TanStack Query (Recommended)

For API data, TanStack Query handles caching, refetching, and loading states:

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch data
const { data: items, isLoading, error } = useQuery({
  queryKey: ['items'],
  queryFn: () => api.getItems(),
  staleTime: 5 * 60 * 1000,  // Consider fresh for 5 min
});

// Mutate data
const queryClient = useQueryClient();
const createItem = useMutation({
  mutationFn: (newItem: Item) => api.createItem(newItem),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['items'] });
    presentToast({ message: 'Item created!', color: 'success' });
  },
});
```

### Global State — Zustand (Recommended)

For client-side global state (auth, preferences, UI state):

```tsx
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Preferences } from '@capacitor/preferences';

// Custom Capacitor storage adapter for Zustand persist
const capacitorStorage = {
  getItem: async (key: string) => {
    const { value } = await Preferences.get({ key });
    return value ? JSON.parse(value) : null;
  },
  setItem: async (key: string, value: string) => {
    await Preferences.set({ key, value });
  },
  removeItem: async (key: string) => {
    await Preferences.remove({ key });
  },
};

interface AuthState {
  user: User | null;
  token: string | null;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: async (credentials) => {
        const { user, token } = await api.login(credentials);
        set({ user, token });
      },
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'auth-storage', storage: capacitorStorage }
  )
);
```

### Context — For Scoped Sharing

Use React Context for data that needs to be shared within a subtree:

```tsx
const ThemeContext = React.createContext<ThemeContextType | null>(null);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDark, setIsDark] = useState(false);

  const toggle = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('ion-palette-dark');
  };

  return (
    <ThemeContext.Provider value={{ isDark, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
};
```

## Form Handling

### React Hook Form + Ionic Components

```tsx
import { useForm, Controller } from 'react-hook-form';

const MyForm: React.FC = () => {
  const { control, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { name: '', email: '', category: '' },
  });

  const onSubmit = (data: FormData) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <IonList>
        <IonItem>
          <Controller
            name="name"
            control={control}
            rules={{ required: 'Name is required' }}
            render={({ field }) => (
              <IonInput
                label="Name"
                labelPlacement="stacked"
                fill="outline"
                value={field.value}
                onIonInput={(e) => field.onChange(e.detail.value)}
                className={errors.name ? 'ion-invalid ion-touched' : ''}
                errorText={errors.name?.message}
              />
            )}
          />
        </IonItem>

        <IonItem>
          <Controller
            name="category"
            control={control}
            render={({ field }) => (
              <IonSelect
                label="Category"
                labelPlacement="stacked"
                value={field.value}
                onIonChange={(e) => field.onChange(e.detail.value)}
              >
                <IonSelectOption value="a">Option A</IonSelectOption>
                <IonSelectOption value="b">Option B</IonSelectOption>
              </IonSelect>
            )}
          />
        </IonItem>
      </IonList>

      <IonButton expand="block" type="submit">Submit</IonButton>
    </form>
  );
};
```

## Component Patterns

### Custom Hook for Capacitor Plugins

```tsx
// hooks/useCamera.ts
import { useState } from 'react';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { useIonToast } from '@ionic/react';

export const useCamera = () => {
  const [photo, setPhoto] = useState<string | null>(null);
  const [presentToast] = useIonToast();

  const takePhoto = async () => {
    try {
      const image = await Camera.getPhoto({
        quality: 90,
        resultType: CameraResultType.Uri,
        source: CameraSource.Prompt,
      });
      setPhoto(image.webPath ?? null);
      return image.webPath;
    } catch (error) {
      if ((error as Error).message !== 'User cancelled photos app') {
        presentToast({ message: 'Camera error', color: 'danger', duration: 2000 });
      }
      return null;
    }
  };

  return { photo, takePhoto };
};
```

### Reusable List Component

```tsx
interface ListItem {
  id: string;
  title: string;
  subtitle?: string;
  image?: string;
}

interface ItemListProps {
  items: ListItem[];
  onItemClick: (id: string) => void;
  onDelete?: (id: string) => void;
}

const ItemList: React.FC<ItemListProps> = ({ items, onItemClick, onDelete }) => (
  <IonList>
    {items.map((item) => (
      <IonItemSliding key={item.id}>
        <IonItem button onClick={() => onItemClick(item.id)}>
          {item.image && (
            <IonThumbnail slot="start">
              <IonImg src={item.image} />
            </IonThumbnail>
          )}
          <IonLabel>
            <h2>{item.title}</h2>
            {item.subtitle && <p>{item.subtitle}</p>}
          </IonLabel>
          <IonIcon icon={chevronForward} slot="end" color="medium" />
        </IonItem>
        {onDelete && (
          <IonItemOptions side="end">
            <IonItemOption color="danger" onClick={() => onDelete(item.id)}>
              <IonIcon icon={trash} slot="icon-only" />
            </IonItemOption>
          </IonItemOptions>
        )}
      </IonItemSliding>
    ))}
  </IonList>
);
```

## Testing

### Component Testing with Vitest + Testing Library

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { IonApp } from '@ionic/react';

// Wrap components in IonApp for testing
const renderWithIonic = (component: React.ReactElement) => {
  return render(<IonApp>{component}</IonApp>);
};

test('renders item list', () => {
  const items = [{ id: '1', title: 'Test Item' }];
  renderWithIonic(<ItemList items={items} onItemClick={vi.fn()} />);
  expect(screen.getByText('Test Item')).toBeInTheDocument();
});
```

### E2E Testing with Cypress/Playwright

```typescript
// Test native-like interactions
test('pull to refresh loads new data', async ({ page }) => {
  await page.goto('/home');
  // Simulate pull-to-refresh gesture
  const content = page.locator('ion-content');
  await content.evaluate((el) => el.scrollTo(0, -100));
  await page.waitForResponse('**/api/items');
});
```
