import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable()
export class WebService {
  movieDB_list: any;
  movie_list: any;
  private movieID: any;

  add_review(review: any) {
    let postData = new FormData();
    postData.append("username", review.username);
    postData.append("review", review.review);
    postData.append("rating", review.rating);

    let today = new Date();
    let todayDate = today.getFullYear() + "-" + today.getMonth() + "-" + today.getDate();
    postData.append("date", todayDate);

    return this.http.post('http://127.0.0.1:5000/api/v1.0/movies/' + this.movieID + '/reviews/', postData);

  }

  constructor(private http: HttpClient) {}

  get_all_items(page: number) {
    return this.http.get('http://127.0.0.1:5000/api/v1.0/movies?pn=' + page)
  }

  show_item(id: any) {
    this.movieID = id;
    return this.http.get('http://127.0.0.1:5000/api/v1.0/movies/' + id);
  }

  get_all_reviews(id: any) {
    return this.http.get('http://127.0.0.1:5000/api/v1.0/movies/' + id + '/reviews/');
 }
}
