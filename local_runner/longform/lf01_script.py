"""
LF01 "How Big Is the Universe? A True-Scale Journey" — script, one entry per spoken sentence.

Scale: Earth (12,742 km) = 1 cm, so 1 cm = 12,742 km. Checked numbers:
  Moon 3,474 km -> 2.7 mm, 384,400 km -> 30.2 cm; light 1.28 s
  Sun 1,392,700 km -> 1.09 m (109 Earths across), 149.6 M km -> 117 m; light 8 min 19 s
  Jupiter 139,820 km -> 11 cm (grapefruit), 778.5 M km -> 611 m; Neptune 30.07 AU -> 3.53 km
  Voyager 1 ~173 AU (Oct 2026, launched Sep 1977, ~17 km/s) -> 20.3 km
  Proxima Centauri 4.2465 ly -> 31,530 km = 79% of Earth's 40,075 km circumference
  Milky Way ~100,000 ly -> 7.4e8 km = 4.96 AU ~ Sun-Jupiter (5.2 AU)
  Andromeda 2.537 Mly -> 126 AU = 3.2x Pluto (39.5 AU), < Voyager 1 (173 AU)
  Observable universe 93 Gly -> 6.9e14 km = 73 light-years
Each beat: text (spoken), chapter (starts a YouTube chapter when set), pause_ms after.
"""

TITLE = "How Big Is the Universe? A True-Scale Journey"
VOICE_RATE = "-4%"

BEATS = [
    # C0 cold open
    dict(ch="The marble", text="Shrink the Earth down to a marble, one centimetre wide."),
    dict(text="Now, let's build the rest of the universe at exactly the same scale."),
    dict(text="Every size, every distance, shrunk by the same amount. Nothing exaggerated."),
    dict(text="By the end of this video, that model won't fit on Earth."),
    dict(text="It won't even fit in our Solar System.", pause_ms=1000),
    # C1 Moon
    dict(ch="The Moon", text="Let's start close to home."),
    dict(text="The Moon becomes a tiny grain, less than three millimetres across."),
    dict(text="And it sits about thirty centimetres away. Roughly the length of a ruler."),
    dict(text="That ruler's length is the farthest any human has ever travelled."),
    dict(text="Twenty four people have crossed it. Only twelve ever stepped out at the other end."),
    dict(text="Light crosses it in just over one second.", pause_ms=1000),
    # C2 Sun
    dict(ch="The Sun", text="Now, the Sun."),
    dict(text="At this scale, it's a glowing ball more than a metre wide."),
    dict(text="You could line up a hundred and nine Earths across its face."),
    dict(text="And if it were hollow, you could pour more than a million Earths inside."),
    dict(text="And it isn't next to us. It's a hundred and seventeen metres away, longer than a football pitch."),
    dict(text="Even light needs eight minutes and twenty seconds to make that trip."),
    dict(text="The sunlight hitting you right now left the Sun before you pressed play.", pause_ms=1000),
    # C3 planets and Voyager
    dict(ch="The edge of the planets", text="Keep walking."),
    dict(text="Jupiter, the giant, is the size of a grapefruit, more than half a kilometre from the Sun."),
    dict(text="Neptune, the last planet, is three and a half kilometres out. A long walk across a city."),
    dict(text="Pluto is a speck of dust, almost five kilometres away."),
    dict(text="And in between, almost nothing. A few tiny balls, scattered across kilometres of empty ground."),
    dict(text="And Voyager One, our farthest spacecraft, after forty nine years of flying at seventeen kilometres every second,"),
    dict(text="is only about twenty kilometres away in our model."),
    dict(text="Everything humanity has ever launched fits inside one small town.", pause_ms=1000),
    # C4 nearest star
    dict(ch="The nearest star", text="Now, the nearest star."),
    dict(text="Proxima Centauri. In our model, it sits thirty one thousand kilometres away."),
    dict(text="That's most of the way around the real Earth."),
    dict(text="Walking there at a normal pace, without ever stopping, would take you most of a year."),
    dict(text="And between here and there, there's nothing. No planets, no stops. Just dark, empty space."),
    dict(text="Its light takes more than four years to reach us."),
    dict(text="Even Voyager, if it were heading that way, would need about seventy thousand years to arrive."),
    dict(text="If you remember one thing from this video, make it this. Space is mostly nothing.", pause_ms=1000),
    # C5 Milky Way
    dict(ch="The Milky Way", text="Our Sun is just one of a few hundred billion stars in the Milky Way."),
    dict(text="Light takes a hundred thousand years to cross it. Longer than farming, longer than writing, longer than history."),
    dict(text="We live about halfway out from the centre, in one of the spiral arms."),
    dict(text="One lap around the galaxy takes the Sun two hundred and thirty million years. The last time we were here, the first dinosaurs were appearing."),
    dict(text="At marble scale, the galaxy no longer fits on Earth."),
    dict(text="It would stretch as far as the real distance from the Sun to Jupiter."),
    dict(text="Our model has outgrown the planet. Now it needs the Solar System to hold it.", pause_ms=1000),
    # C6 Andromeda
    dict(ch="Andromeda", text="And the Milky Way isn't alone."),
    dict(text="Andromeda, our nearest big neighbour, is two and a half million light years away."),
    dict(text="In our model, that's about a hundred and twenty five times the distance from Earth to the Sun."),
    dict(text="Three times farther than Pluto."),
    dict(text="And here's the strange part. That's still closer than Voyager One really is, right now.", pause_ms=1000),
    dict(text="It's the most distant thing you can see with your own eyes. A faint smudge on a dark night."),
    dict(text="The light you'd see left it before our species even existed."),
    dict(text="And it's coming our way. In four or five billion years, the two galaxies will merge.", pause_ms=1000),
    # C7 observable universe
    dict(ch="The observable universe", text="Now, zoom out all the way."),
    dict(text="This is one tiny patch of sky, photographed by Hubble. Almost every dot is a galaxy, each with billions of stars."),
    dict(text="Hubble stared at this one spot, smaller than a grain of sand held at arm's length, for more than eleven days."),
    dict(text="The light from the faintest ones left them more than thirteen billion years ago."),
    dict(text="The observable universe holds hundreds of billions of galaxies, spread across ninety three billion light years."),
    dict(text="Build that at our scale, and the model is seventy three light years wide."),
    dict(text="Light itself would need seventy three years to cross it. Longer than most human lives.", pause_ms=900),
    dict(text="And that's only the part we can see. The universe may go on far beyond it.", pause_ms=1000),
    # C8 ending
    dict(ch="That's us", text="A model so big that light needs a lifetime to cross it."),
    dict(text="And somewhere in the middle, one marble, one centimetre wide."),
    dict(text="Every person you've ever known, every song, every story, all on that one marble."),
    dict(text="That's us.", pause_ms=300),
]
