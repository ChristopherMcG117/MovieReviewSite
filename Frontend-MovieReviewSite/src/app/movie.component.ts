import { Component } from '@angular/core';
import { WebService } from './web.service';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, Validators } from '@angular/forms';
import { AuthService } from '@auth0/auth0-angular';

@Component({
  selector: 'movie',
  templateUrl: './movie.component.html',
  styleUrls: ['./movie.component.css']
})
export class MovieComponent {
  movie_list: any;
  reviews: any = [];
  reviewForm: any;

  onSubmit() {
    this.webService.add_review(this.reviewForm.value)
    .subscribe((response: any) => {
      this.reviewForm.reset();
      this.reviews = this.webService.get_all_reviews(
        this.route.snapshot.params['id']);
    });

 }

 isInvalid(control: any) {
  return this.reviewForm.controls[control].invalid &&
    this.reviewForm.controls[control].touched;
 }

 isUntouched() {
  return this.reviewForm.controls.username.pristine ||
    this.reviewForm.controls.review.pristine;
 }

 isIncomplete() {
  return this.isInvalid('username') ||
    this.isInvalid('review') ||
    this.isUntouched();
 }

  constructor(private webService: WebService,
              private route: ActivatedRoute,
              private formBuilder: FormBuilder,
              public authService: AuthService) {}

  ngOnInit() {

  this.reviewForm = this.formBuilder.group({
    username: ['', Validators.required],
    review: ['', Validators.required],
    rating: 10
 });

  this.movie_list = this.webService.show_item(this.route.snapshot.params['id']);

  this.reviews = this.webService.get_all_reviews(this.route.snapshot.params['id']);

  }
}
