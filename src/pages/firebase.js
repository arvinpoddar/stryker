import firebase from 'firebase'

const config = {
  apiKey: 'AIzaSyBSwh190vKk4hnE8Tfcewi-HpNeRLFv5XI',
  authDomain: 'stryker-c841b.firebaseapp.com',
  databaseURL: 'https://stryker-c841b.firebaseio.com',
  projectId: 'stryker-c841b',
  storageBucket: 'stryker-c841b.appspot.com',
  messagingSenderId: '976906995305',
  appId: '1:976906995305:web:99ec232f50695f8d0dc4f8',
  measurementId: 'G-TSX24R7V0P'
}

export default !firebase.apps.length
  ? firebase.initializeApp(config)
  : firebase.app()
