import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { MoviesComponent } from './movies.component';
import { MovieComponent } from './movie.component';
import { WebService } from './web.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { HomeComponent } from './home.component';
import { ReactiveFormsModule } from '@angular/forms';
import { AuthModule } from '@auth0/auth0-angular';
import { NavComponent } from './nav.component';



var routes: any = [
 {
  path: '',
  component: HomeComponent
 },
 {
  path: 'movies',
  component: MoviesComponent
 },
 {
 path: 'movies/:id',
 component: MovieComponent
 },
];

@NgModule({
  declarations: [
    AppComponent, MoviesComponent, MovieComponent, HomeComponent, NavComponent
  ],
  imports: [
    BrowserModule, HttpClientModule, ReactiveFormsModule,
    RouterModule.forRoot(routes),
    AuthModule.forRoot( { domain:'dev-krv0sjac8tv2rgdn.us.auth0.com', clientId: 'SGadiEPNbhSvJnjed5cI8N3HTwWjrsj8'})
  ],
  providers: [WebService],
  bootstrap: [AppComponent]
})
export class AppModule { }
