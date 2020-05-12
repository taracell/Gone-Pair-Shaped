# Cardboard Against Humankind - Cards Against Humanity over Discord.
*presented by ClicksMinutePer*


[![Discord Bots](https://top.gg/api/widget/status/679361555732627476.svg?noavatar=true)](https://top.gg/bot/679361555732627476)
[![Discord Bots](https://top.gg/api/widget/servers/679361555732627476.svg?noavatar=true)](https://top.gg/bot/679361555732627476)
[![Discord Bots](https://top.gg/api/widget/upvotes/679361555732627476.svg?noavatar=true)](https://top.gg/bot/679361555732627476/vote)
[![Discord Bots](https://top.gg/api/widget/lib/679361555732627476.svg?noavatar=true)](https://top.gg/bot/679361555732627476)

> **High Uptime** 
> ====
> Cardboard Against Humankind will go down into maintinance mode for a short amount of time. Games cannot be started in this period 
> and current games will be left to finish.


> **Low Latency** 
> ====
> The average ping time of the bot is around 15ms, allowing you to play games with little delay.


> **Custom Cards** 
> ====
> **[Cardcast](https://cardcastgame.com/)** decks are now supported and can be used in games. This allows you to create a free deck
> and use inside jokes in your own server. These decks can be marked as unlisted so only you can see and use them.
> *Both black and white cards are supported.* Check the **What packs?** section for how to add them.


> **Customisable**
> ====
> Customise your game with every option from shuffles to player timeouts. Access them all through `$play true`


## Before you play...
#### Once you add the bot there are a couple of things you might want to do.

<dl>
  <dt><h3>Accept the terms</h3></dt>
  <dd>To use msot commands, you need to accept the <code>$terms</code> by reacting with the tick. This can only be done by people with the <b>Manage Server</b> permission.</dd>
  <hr>
  <dt><h3>Set a prefix</h3></dt>
  <dd>You can set a prefix by using <code>$setprefix </code> followed by the prefixes you want to use, separated by spaces. To add a prefix with a space in, surround it with "" or ''.<br>
  If any issues happen with the prefix, pinging the bot will always work and cannot be disabled. So if you ever forget the prefix, you can @ the bot and <code>setprefix</code></dd>
  <hr>
  <dt><h3>Choose a language</h3></dt>
  <dd>Some languages are now supported in the bot. These can be added over time and can be viewed in <code>$lang</code> and reacting with the language you want to use.</dd>
</dl>

<hr>

## Let's play!
#### It's time to start a game - How is this done?

<dl>
  <dt>
    <h3>
      Start the game
    </h3>
  </dt>
  <dd>
    Firstly, you need to run <code>$play</code> to play a game. You will then be walked through all of the different options. If you want more options, do <code>$play true</code>.
  </dd>
  <hr>
  <dt><h3>How do you win?</h3></dt>
  <dd>Select how many points a user needs to win the game by typing it in chat. It can be anywhere from <code>1</code> to <code>100</code>, or you can choose <code>0</code> for an endless game.</dd>
  <hr>
  <dt>
    <h3>
      Which packs?
    </h3>
  </dt>
  <dd>
    There are a lot of packs to choose from in <code>$packs</code>, so how do you select them?<br><br>
    Adding specific packs: If you want Base, Base 2 and Ex1, you type <code>base base2 ex1</code>.<br>
    Adding all packs: If you just want every pack, go ahead and type <code>all</code>.<br>
    Removing a pack: If you want to have every pack, but not anime, you type <code>all -anime</code>.<br>
    Adding a <b>Cardcast</b> deck: At the end of your packs message, you need to put the deck code. This will be a 5 character code to identify the pack. If you want all packs, but not anime, and deck "12ABC", you type <code>all -anime 12ABC</code>.<br><br>
    <b>Notes</b>: Any amount of packs can be removed with a minus, it is typed as <code>all -anime -ex1 -ex2</code>. Multiple Cardcast decks can be added, just typed as normal decks with spaces in between <code>base base2 AB123 45CDE</code>. Non Cardcast decks must be typed in lower case, and Cardcast codes in UPPER CASE.
  </dd>
  <hr>
  <details>
    <summary>
      Advanced play options
    </summary>
    <h4>Can we train out bot?</h4> - Type <code>yes</code> or <code>no</code> to choose if we can use your game to train bots.<br>
    <h4>Want it to be anonymous?</h4> - Type <code>yes</code> or <code>no</code> to choose if the winners and leaderboard should be hidden until the end.<br>
    <h4>How big should your hand be?</h4> - Type a number from 1 to 25 to choose how many cards each player chooses from.<br>
    <h4>How many rounds should I end after?</h4> - Type a number from 0 to 200 to choose how many rounds there should be. 0 rounds means there is no limit.<br>
    <h4>How many times would you like to be able to shuffle?</h4> - 0 to 50, allows users to do <code>$shuffle</code> in the chat to get rid of all of their cards and get new ones.<br>
    <h4>How long should you get to pick your cards?</h4> - 10 to 600 seconds, the amount of time before a player is kicked for innactivity when picking their cards.<br>
    <h4>How long should the tsar get to pick the best card?</h4> - 10 to 600 seconds, the amount of time the tsar has before being kicked for innactivity when picking the winner.<br></dd>
    <h4>How long should we wait between rounds?</h4> - A number from 0 to 150 seconds. Tells the bot how long to wait before starting another round when the winner is picked.<br>
  </details>
  <hr>
  <dt><h3>Join the game</h3></dt>
  <dd>
    In order to join a game, you do <code>$join</code> and you will be added to the game in that channel. This can be during the startup time, or in the middle of the game.
  </dd>
  <dt><h3>Picking your cards</h3></dt>
  <dd>
    So the time has come - you need to choose your cards. You will recieve a DM from the bot with a list of your cards. All you need to do is send the number of the card you want to pick. Each card has a number before it, and will just type this number.<br>
    If you need to pick 2 cards this round, just choose the first card, and the second card in a new message. The numbers will not change when this happens.
  </dd>
  <dt><h3>Picking the winner</h3></dt>
  <dd>
    The winner is chosen in the exact same way. Pick the best answer by its number in your DM. Cards which have 2(or more) answers are separated by a <code>|</code>.
  </dd>
  <dt><h3>Want to leave?</h3></dt>
  <dd>
    If you don't want to play anymore, or need to go, just do <code>$leave</code> in the channel with the game and you will be removed.
  </dd>
  <dt><h3>Time to end the game?</h3></dt>
  <dd>
    Ending a game can be done by typing <code>$end></code>. This ends the game when the current round finishes. To end the game instantly, run <code>$end true</code>.
  </dd>
</dl>

<hr>

## This bot was made by ClicksMinutePer:
#### Cardboard Against Humankind Dev Team:
PineappleFan#9955 and Minion3665#6456, TheCodedProf#2583, DOSmile#7021 and EEKIM10_YT#4015

*This bot is not associated with Cards Against Humanity LLC*
