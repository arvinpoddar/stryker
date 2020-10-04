<template>
  <q-page class="ultra">
    <div class="center">
      <div class="logo">
        <img alt="Quasar logo" src="~assets/logo.png" />
      </div>

      <div class="game-info">
        <div class="section shadow-3 score-cards">
          <div class="score">
            <div class="white-score">
              <q-btn
                icon="expand_less"
                color="blue-grey-11"
                text-color="black"
                @click="increment('white', 1)"
              />
              <div class="score-font">{{ whiteScore }}</div>
              <q-btn
                icon="expand_more"
                color="blue-grey-11"
                text-color="black"
                @click="increment('white', -1)"
              />
            </div>

            <div class="black-score">
              <q-btn
                icon="expand_less"
                color="blue-grey-11"
                text-color="black"
                @click="increment('black', 1)"
              />
              <div class="score-font">{{ blackScore }}</div>
              <q-btn
                icon="expand_more"
                color="blue-grey-11"
                text-color="black"
                @click="increment('black', -1)"
              />
            </div>
          </div>
        </div>
        <div class="stats">
          <div class="section shadow-3 game-stats">
            <div class="text-h6">Game Stats:</div>
            <div class="rounded">Game Duration: {{ duration }} secs</div>
            <div class="rounded">
              White Possession: {{ whitePossession }} secs ({{
                whitePossessionPercent
              }}%)
            </div>
            <div class="rounded">
              Black Possession: {{ blackPossession }} secs ({{
                blackPossessionPercent
              }}%)
            </div>

            <q-separator class="q-my-md" />

            <div class="text-h6">Score Feed:</div>
            <div class="score-feed">
              <div
                class="score-row row items-center"
                v-for="(s, i) in scoreFeed"
                :key="i"
              >
                <div v-if="typeof s === 'string'">
                  POINT ADJUST ({{}})
                </div>
                <div class="col">
                  <span v-if="s.scorer">
                    <span v-if="s.goalSpeed">
                      <b>{{ s.scorer }}</b> Scored! ({{ s.goalSpeed }} ft/sec)
                    </span>
                    <span v-else>
                      <b>{{ s.scorer }}</b> Scored! (Point Adjustment)
                    </span>
                  </span>
                  <span v-else>
                    <b>Point Adjustment</b>
                  </span>
                </div>
                <div>({{ s.whiteScore }} - {{ s.blackScore }})</div>
              </div>
              <div class="score-row" v-if="!scoreFeed.length">
                <em>No points scored yet!</em>
              </div>
            </div>
          </div>
          <q-btn
            color="negative"
            @click="resetGame"
            icon="refresh"
            label="Reset Game"
            class="q-mt-md"
          />
        </div>
      </div>
    </div>
  </q-page>
</template>

<script>
/* eslint-disable no-unused-vars */
import firebase from './firebase.js'

export default {
  name: 'Main',
  data () {
    return {
      db: null,
      blackScore: 0,
      whiteScore: 0,
      duration: 0,
      blackPossession: 0,
      whitePossession: 0,
      scoreFeed: [],
      scoreAdjusted: false
    }
  },
  computed: {
    blackPossessionPercent () {
      if (!(this.blackPossession || this.duration)) {
        return 0.0
      }
      return ((this.blackPossession / this.duration) * 100).toFixed(2)
    },

    whitePossessionPercent () {
      if (!(this.whitePossession || this.duration)) {
        return 0.0
      }
      return ((this.whitePossession / this.duration) * 100).toFixed(2)
    }
  },

  methods: {
    increment (color, amount) {
      if (color === 'black') {
        this.blackScore = Math.max(this.blackScore + amount, 0)
        this.db.ref('BLACK_GOALS').set(this.blackScore)
      } else if (color === 'white') {
        this.whiteScore = Math.max(this.whiteScore + amount, 0)
        this.db.ref('WHITE_GOALS').set(this.whiteScore)
      }

      if (amount < 0) {
        const pos = this.scoreFeed.findIndex(
          obj => obj.scorer.toLowerCase() === color
        )
        if (pos >= 0) {
          const res = [
            ...this.scoreFeed.slice(0, pos),
            ...this.scoreFeed.slice(pos + 1, this.scoreFeed.length)
          ].reverse()
          this.db.ref('GOALS').set(res)
        }
      } else {
        const res = [
          {
            blackScore: this.blackScore,
            whiteScore: this.whiteScore,
            scorer: color === 'black' ? 'Black' : 'White',
            goalSpeed: 0
          },
          ...this.scoreFeed
        ].reverse()
        this.db.ref('GOALS').set(res)
      }
    },

    resetGame () {
      this.$q
        .dialog({
          title: 'Confirm',
          message: 'Are you sure you want to reset the game?',
          cancel: true
        })
        .onOk(() => {
          this.db.ref('RESET').set(true)
        })
    }
  },
  mounted () {
    // set up connection to databas
    this.db = firebase.database()

    // set up listeners for realtime changes in firebase
    this.db.ref('DURATION').on('value', value => {
      this.duration = value.val()
    })

    this.db.ref('BLACK_POSSESSION').on('value', value => {
      this.blackPossession = value.val()
    })

    this.db.ref('WHITE_POSSESSION').on('value', value => {
      this.whitePossession = value.val()
    })

    this.db.ref('GOALS').on('value', value => {
      console.log(this.scoreFeed)
      this.scoreFeed = (value.val() || []).reverse()
      this.blackScore = this.scoreFeed.filter(s => s.scorer === 'Black').length
      this.whiteScore = this.scoreFeed.filter(s => s.scorer === 'White').length
    })
  }
}
</script>

<style lang="scss">
.ultra {
  width: 100%;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #ebf1fe;
  .center {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    .logo {
      width: 100%;
      text-align: center;
      margin-bottom: 20px;
      img {
        width: 100%;
        max-width: 400px;
      }
    }

    .game-info {
      width: 100%;
      display: grid;
      grid-template-columns: 2fr 1fr;
      column-gap: 10px;
      max-width: 1100px;
      .section {
        background-color: #fff;
        border-radius: 5px;
      }
      .score-cards {
        display: flex;
        justify-content: center;
        padding: 20px 10px;
        background-color: $green-9;
        background-image: url("../assets/soccer-field.jpg");
        background-size: 100% 100%;
        .score {
          display: flex;
          align-items: center;
          gap: 80px;
        }

        .score-font {
          font-size: 180px;
          align-items: center;
          justify-content: center;
        }

        .white-score {
          color: white;
          -webkit-text-fill-color: white; /* Will override color (regardless of order) */
          -webkit-text-stroke-width: 1px;
          -webkit-text-stroke-color: black;
          display: flex;
          flex-direction: column;
          text-align: center;
          min-width: 202px;
        }

        .black-score {
          display: flex;
          flex-direction: column;
          text-align: center;
          min-width: 202px;
        }
      }

      .stats {
        display: flex;
        flex-direction: column;

        .game-stats {
          padding: 10px;
          flex: 1;
          .score-feed {
            max-height: 150px;
            overflow-y: auto;
            .score-row {
              border-radius: 4px;
              border: 1px solid #cecece;
              background-color: #ebf1fe;
              padding: 8px 5px;
              margin-bottom: 5px;
            }
          }
        }
      }
    }
  }
}

@media only screen and (max-width: 1000px) {
.ultra {
  .center {
    .game-info {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr 1fr;
      column-gap: 0px;
      row-gap: 20px;
    }
  }
}
}
</style>
