# Ionic Angular Reference

## Table of Contents
1. [Project Setup](#project-setup)
2. [Standalone Components](#standalone-components)
3. [Routing and Guards](#routing-and-guards)
4. [Ionic Lifecycle](#ionic-lifecycle)
5. [State Management with Signals](#state-management-with-signals)
6. [Services and Dependency Injection](#services-and-dependency-injection)
7. [Form Handling](#form-handling)
8. [Component Patterns](#component-patterns)
9. [Testing](#testing)

---

## Project Setup

```bash
ionic start myApp tabs --type=angular
cd myApp
ionic serve
```

### Key Dependencies

```json
{
  "@ionic/angular": "^8.x",
  "@angular/core": "^19.x",
  "@angular/router": "^19.x",
  "ionicons": "^7.x"
}
```

### App Bootstrap (Standalone)

Modern Ionic Angular uses standalone components — no NgModules needed:

```typescript
// main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { provideRouter } from '@angular/router';
import { routes } from './app/app.routes';
import { AppComponent } from './app/app.component';

bootstrapApplication(AppComponent, {
  providers: [
    provideIonicAngular({}),
    provideRouter(routes),
    provideHttpClient(),
  ],
});
```

```typescript
// app.component.ts
import { Component } from '@angular/core';
import { IonApp, IonRouterOutlet } from '@ionic/angular/standalone';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [IonApp, IonRouterOutlet],
  template: `
    <ion-app>
      <ion-router-outlet></ion-router-outlet>
    </ion-app>
  `,
})
export class AppComponent {}
```

## Standalone Components

Import Ionic components individually in each component that uses them:

```typescript
import { Component } from '@angular/core';
import {
  IonHeader, IonToolbar, IonTitle, IonContent,
  IonList, IonItem, IonLabel, IonButton, IonIcon,
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { heart, heartOutline, trash } from 'ionicons/icons';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent,
    IonList, IonItem, IonLabel, IonButton, IonIcon,
  ],
  template: `
    <ion-header>
      <ion-toolbar>
        <ion-title>Home</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content>
      <ion-list>
        @for (item of items(); track item.id) {
          <ion-item>
            <ion-label>{{ item.name }}</ion-label>
            <ion-button fill="clear" slot="end" (click)="delete(item.id)">
              <ion-icon name="trash" slot="icon-only"></ion-icon>
            </ion-button>
          </ion-item>
        }
      </ion-list>
    </ion-content>
  `,
})
export class HomePage {
  items = signal<Item[]>([]);

  constructor() {
    addIcons({ heart, heartOutline, trash });
  }

  delete(id: string) {
    this.items.update(items => items.filter(i => i.id !== id));
  }
}
```

Register icons with `addIcons()` in the constructor — this is how standalone Ionic Angular handles Ionicons.

## Routing and Guards

### Route Configuration

```typescript
// app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'tabs',
    pathMatch: 'full',
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.page').then(m => m.LoginPage),
  },
  {
    path: 'tabs',
    loadComponent: () => import('./pages/tabs/tabs.page').then(m => m.TabsPage),
    canActivate: [authGuard],
    children: [
      {
        path: 'home',
        loadComponent: () => import('./pages/home/home.page').then(m => m.HomePage),
      },
      {
        path: 'search',
        loadComponent: () => import('./pages/search/search.page').then(m => m.SearchPage),
      },
      {
        path: 'profile',
        loadComponent: () => import('./pages/profile/profile.page').then(m => m.ProfilePage),
      },
      {
        path: '',
        redirectTo: 'home',
        pathMatch: 'full',
      },
    ],
  },
];
```

### Tabs Page

```typescript
// pages/tabs/tabs.page.ts
import { Component } from '@angular/core';
import { IonTabs, IonTabBar, IonTabButton, IonIcon, IonLabel } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { home, search, person } from 'ionicons/icons';

@Component({
  selector: 'app-tabs',
  standalone: true,
  imports: [IonTabs, IonTabBar, IonTabButton, IonIcon, IonLabel],
  template: `
    <ion-tabs>
      <ion-tab-bar slot="bottom">
        <ion-tab-button tab="home">
          <ion-icon name="home"></ion-icon>
          <ion-label>Home</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="search">
          <ion-icon name="search"></ion-icon>
          <ion-label>Search</ion-label>
        </ion-tab-button>
        <ion-tab-button tab="profile">
          <ion-icon name="person"></ion-icon>
          <ion-label>Profile</ion-label>
        </ion-tab-button>
      </ion-tab-bar>
    </ion-tabs>
  `,
})
export class TabsPage {
  constructor() {
    addIcons({ home, search, person });
  }
}
```

### Functional Route Guards

```typescript
// guards/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree(['/login']);
};
```

### Programmatic Navigation

```typescript
import { NavController } from '@ionic/angular/standalone';

@Component({ /* ... */ })
export class MyPage {
  private navCtrl = inject(NavController);

  goToDetail(id: string) {
    this.navCtrl.navigateForward(`/detail/${id}`);
  }

  goBack() {
    this.navCtrl.back();
  }

  goToRoot() {
    this.navCtrl.navigateRoot('/tabs/home');
  }
}
```

## Ionic Lifecycle

Angular Ionic pages support special lifecycle hooks because pages stay in the DOM for back-navigation:

```typescript
import { ViewWillEnter, ViewDidEnter, ViewWillLeave, ViewDidLeave } from '@ionic/angular';

@Component({ /* ... */ })
export class MyPage implements ViewWillEnter, ViewDidEnter, ViewWillLeave, ViewDidLeave {
  ionViewWillEnter() {
    // Page is about to become active — fetch fresh data
    this.loadData();
  }

  ionViewDidEnter() {
    // Page is now active and visible — start animations, analytics
    this.analyticsService.trackView('my-page');
  }

  ionViewWillLeave() {
    // Page is about to leave — save drafts, pause media
    this.saveDraft();
  }

  ionViewDidLeave() {
    // Page has left — cleanup subscriptions
    this.subscription?.unsubscribe();
  }
}
```

Use these instead of `ngOnInit`/`ngOnDestroy` for view-specific logic. `ngOnInit` only fires once; Ionic lifecycle hooks fire every time the view enters/leaves.

## State Management with Signals

Angular 19+ signals are the recommended approach for reactive state:

### Component-Level Signals

```typescript
@Component({ /* ... */ })
export class HomePage {
  // Writable signals
  items = signal<Item[]>([]);
  searchTerm = signal('');
  isLoading = signal(false);

  // Computed signals (derived state)
  filteredItems = computed(() =>
    this.items().filter(item =>
      item.name.toLowerCase().includes(this.searchTerm().toLowerCase())
    )
  );

  itemCount = computed(() => this.filteredItems().length);

  // Effects for side effects
  constructor() {
    effect(() => {
      // Runs whenever searchTerm changes
      console.log('Search:', this.searchTerm());
    });
  }

  addItem(item: Item) {
    this.items.update(items => [...items, item]);
  }

  removeItem(id: string) {
    this.items.update(items => items.filter(i => i.id !== id));
  }
}
```

### Signal-Based Service (Global State)

```typescript
// services/auth.service.ts
import { Injectable, signal, computed } from '@angular/core';
import { Preferences } from '@capacitor/preferences';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private userSignal = signal<User | null>(null);
  private tokenSignal = signal<string | null>(null);

  // Public read-only access
  user = this.userSignal.asReadonly();
  isAuthenticated = computed(() => this.tokenSignal() !== null);

  async login(credentials: Credentials): Promise<void> {
    const response = await this.http.post<AuthResponse>('/api/login', credentials);
    this.userSignal.set(response.user);
    this.tokenSignal.set(response.token);
    await Preferences.set({ key: 'token', value: response.token });
  }

  async logout(): Promise<void> {
    this.userSignal.set(null);
    this.tokenSignal.set(null);
    await Preferences.remove({ key: 'token' });
  }

  async restoreSession(): Promise<void> {
    const { value } = await Preferences.get({ key: 'token' });
    if (value) {
      this.tokenSignal.set(value);
      // Fetch user profile...
    }
  }
}
```

### Resource API (Angular 19+ — Server State)

```typescript
import { resource } from '@angular/core';

@Component({ /* ... */ })
export class ItemsPage {
  private categoryId = signal('all');

  // Reactive data fetching — re-fetches when categoryId changes
  itemsResource = resource({
    request: () => this.categoryId(),
    loader: async ({ request: category }) => {
      const response = await fetch(`/api/items?category=${category}`);
      return response.json() as Promise<Item[]>;
    },
  });

  // Access in template:
  // @if (itemsResource.isLoading()) { <ion-spinner /> }
  // @for (item of itemsResource.value() ?? []; track item.id) { ... }
}
```

## Services and Dependency Injection

### Data Service Pattern

```typescript
// services/items.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class ItemsService {
  private http = inject(HttpClient);
  private baseUrl = '/api/items';

  getItems() {
    return this.http.get<Item[]>(this.baseUrl);
  }

  getItem(id: string) {
    return this.http.get<Item>(`${this.baseUrl}/${id}`);
  }

  createItem(item: Partial<Item>) {
    return this.http.post<Item>(this.baseUrl, item);
  }

  updateItem(id: string, item: Partial<Item>) {
    return this.http.put<Item>(`${this.baseUrl}/${id}`, item);
  }

  deleteItem(id: string) {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}
```

### HTTP Interceptor for Auth

```typescript
// interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.token();

  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(req);
};

// Register in main.ts:
// provideHttpClient(withInterceptors([authInterceptor]))
```

## Form Handling

### Reactive Forms with Ionic

```typescript
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

@Component({
  standalone: true,
  imports: [
    ReactiveFormsModule,
    IonList, IonItem, IonInput, IonSelect, IonSelectOption,
    IonButton, IonNote,
  ],
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <ion-list>
        <ion-item>
          <ion-input
            formControlName="name"
            label="Name"
            labelPlacement="stacked"
            fill="outline"
            [errorText]="form.controls.name.errors?.['required'] ? 'Required' : ''"
            [class.ion-invalid]="form.controls.name.touched && form.controls.name.invalid"
            [class.ion-touched]="form.controls.name.touched"
          ></ion-input>
        </ion-item>

        <ion-item>
          <ion-input
            formControlName="email"
            label="Email"
            labelPlacement="stacked"
            fill="outline"
            type="email"
          ></ion-input>
        </ion-item>

        <ion-item>
          <ion-select
            formControlName="role"
            label="Role"
            labelPlacement="stacked"
          >
            <ion-select-option value="user">User</ion-select-option>
            <ion-select-option value="admin">Admin</ion-select-option>
          </ion-select>
        </ion-item>
      </ion-list>

      <ion-button expand="block" type="submit" [disabled]="form.invalid">
        Save
      </ion-button>
    </form>
  `,
})
export class MyFormPage {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    role: ['user', Validators.required],
  });

  onSubmit() {
    if (this.form.valid) {
      console.log(this.form.value);
    }
  }
}
```

## Component Patterns

### Smart/Presentational Split

```typescript
// Smart component — handles data and logic
@Component({
  selector: 'app-item-list-page',
  standalone: true,
  imports: [ItemListComponent, IonPage, IonContent, IonHeader, IonToolbar, IonTitle],
  template: `
    <ion-page>
      <ion-header>
        <ion-toolbar>
          <ion-title>Items</ion-title>
        </ion-toolbar>
      </ion-header>
      <ion-content>
        <app-item-list
          [items]="items()"
          [loading]="isLoading()"
          (itemSelected)="onSelect($event)"
          (itemDeleted)="onDelete($event)"
        />
      </ion-content>
    </ion-page>
  `,
})
export class ItemListPage {
  private itemsService = inject(ItemsService);
  items = signal<Item[]>([]);
  isLoading = signal(true);

  constructor() {
    this.loadItems();
  }

  async loadItems() {
    this.isLoading.set(true);
    this.items.set(await firstValueFrom(this.itemsService.getItems()));
    this.isLoading.set(false);
  }
}

// Presentational component — pure rendering
@Component({
  selector: 'app-item-list',
  standalone: true,
  imports: [IonList, IonItem, IonLabel, IonSkeletonText, IonItemSliding, IonItemOptions, IonItemOption],
  template: `
    @if (loading) {
      <ion-list>
        @for (i of [1,2,3,4,5]; track i) {
          <ion-item>
            <ion-label>
              <h2><ion-skeleton-text [animated]="true" style="width: 60%"></ion-skeleton-text></h2>
              <p><ion-skeleton-text [animated]="true" style="width: 80%"></ion-skeleton-text></p>
            </ion-label>
          </ion-item>
        }
      </ion-list>
    } @else {
      <ion-list>
        @for (item of items; track item.id) {
          <ion-item-sliding>
            <ion-item (click)="itemSelected.emit(item)">
              <ion-label>
                <h2>{{ item.name }}</h2>
                <p>{{ item.description }}</p>
              </ion-label>
            </ion-item>
            <ion-item-options side="end">
              <ion-item-option color="danger" (click)="itemDeleted.emit(item.id)">
                Delete
              </ion-item-option>
            </ion-item-options>
          </ion-item-sliding>
        }
      </ion-list>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ItemListComponent {
  @Input() items: Item[] = [];
  @Input() loading = false;
  @Output() itemSelected = new EventEmitter<Item>();
  @Output() itemDeleted = new EventEmitter<string>();
}
```

### Using OnPush Change Detection

All presentational components should use `OnPush` for performance. Combined with signals, this eliminates unnecessary change detection cycles:

```typescript
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  // ...
})
```

## Testing

### Component Testing

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';

describe('HomePage', () => {
  let component: HomePage;
  let fixture: ComponentFixture<HomePage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomePage],
      providers: [
        provideIonicAngular(),
        { provide: ItemsService, useValue: mockItemsService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomePage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load items on view enter', () => {
    component.ionViewWillEnter();
    expect(component.items().length).toBeGreaterThan(0);
  });
});
```
