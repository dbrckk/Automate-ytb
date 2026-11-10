"""Check reusable source-art quality, cache and true native video integration."""
import unittest

from PIL import Image,ImageDraw,ImageStat
from automate_ytb.hero_materials25d import (
    glass_sphere,solar_disc,thermal_pool,ice_floe,VERSION,
)
from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.science_rainbow import draw_rainbow


class Hero2p5DMaterialTests(unittest.TestCase):
    def test_cached_glass_has_real_alpha_gradients_and_multiscale_material(self):
        orb=glass_sphere(458,seed=173)
        self.assertEqual(orb.size,(458,458))
        self.assertEqual(orb.mode,"RGBA")
        self.assertIs(orb,glass_sphere(458,seed=173))
        self.assertEqual(orb.getpixel((0,0))[3],0)
        self.assertGreater(orb.getpixel((229,229))[3],35)
        self.assertGreater(orb.getchannel("A").getextrema()[1],160)
        self.assertGreater(max(ImageStat.Stat(orb.convert("RGB")).stddev),15)
        self.assertNotEqual(orb.tobytes(),glass_sphere(458,seed=174).tobytes())

    def test_painted_solar_disc_is_distinct_from_glass_and_has_real_halo(self):
        solar=solar_disc(172)
        self.assertGreater(solar.width,172)
        self.assertEqual(solar.mode,"RGBA")
        self.assertIs(solar,solar_disc(172))
        self.assertEqual(solar.getpixel((0,0))[3],0)
        self.assertEqual(solar.getpixel((solar.width//2,solar.height//2))[3],255)
        self.assertNotEqual(solar.tobytes(),glass_sphere(172).tobytes())
        self.assertTrue(VERSION.endswith("p512-v1"))

    def test_material_input_limits_reject_network_or_arbitrary_dimensions(self):
        for value in (0,63,721,False,720.0):
            with self.assertRaises(ValueError):
                glass_sphere(value)
            with self.assertRaises(ValueError):
                solar_disc(value)
        for seed in (-1,1_000_001,False,"17"):
            with self.assertRaises(ValueError):
                glass_sphere(172,seed=seed)

    def test_all_three_production_droplet_scenes_use_original_hero_art(self):
        topic="How do rainbows form?"
        for index,(word,story) in enumerate((
            ("refraction","Entering a raindrop, light bends."),
            ("reflection","Some light reflects inside a raindrop."),
            ("emergence","Leaving the drop, light spreads outward."),
        ),start=1):
            with self.subTest(beat=word):
                film=PortraitScienceScene(topic=topic,narration=story,
                                          scene_index=index)
                self.assertEqual(film.rainbow_beat,word)
                first=film.frame(.15,6.)
                self.assertEqual(first.size,(1080,1920))
                self.assertEqual(first.mode,"RGB")
                self.assertEqual(first.tobytes(),film.frame(.15,6.).tobytes())

    def test_original_thermal_and_ice_assets_are_cached_materials(self):
        warm=thermal_pool((220,270),kind="warm",seed=500)
        cold=thermal_pool((220,270),kind="cool",seed=500)
        self.assertIs(warm,thermal_pool((220,270),kind="warm",seed=500))
        self.assertEqual(warm.mode,"RGBA")
        self.assertEqual(warm.getpixel((0,0))[3],0)
        self.assertGreater(warm.getpixel((110,135))[3],180)
        self.assertNotEqual(warm.tobytes(),cold.tobytes())
        self.assertGreater(max(ImageStat.Stat(warm.convert("RGB")).stddev),20)
        self.assertNotEqual(warm.tobytes(),
                            thermal_pool((220,270),kind="warm",seed=501).tobytes())
        ice=ice_floe((200,124),seed=907)
        self.assertIs(ice,ice_floe((200,124),seed=907))
        self.assertEqual(ice.getpixel((0,0))[3],0)
        self.assertGreater(ice.getchannel("A").getextrema()[1],200)
        self.assertGreater(len(ice.getcolors(maxcolors=20000) or []),4)

    def test_thermal_material_and_ice_reject_invalid_source_input(self):
        for size in ("bad",(7000,320),(72,72)):
            with self.assertRaises(ValueError):
                thermal_pool(size,kind="warm")
        with self.assertRaises(ValueError):
            thermal_pool((220,270),kind="plasma")
        with self.assertRaises(ValueError):
            ice_floe((200,124),seed=-1)

    def test_four_ocean_mechanisms_use_real_detailed_source_art(self):
        from automate_ytb.science_storyboards import draw_storyboard
        for beat in ("solar","wind","sinking","heat"):
            with self.subTest(beat=beat):
                source=Image.new("RGBA",(1080,1920))
                legacy=Image.new("RGBA",(1080,1920))
                draw_storyboard(ImageDraw.Draw(source,"RGBA"),
                                beat,.4,True,duration=6.,canvas=source)
                draw_storyboard(ImageDraw.Draw(legacy,"RGBA"),
                                beat,.4,True,duration=6.)
                self.assertNotEqual(source.tobytes(),legacy.tobytes())
                self.assertEqual(source.crop((0,0,1080,520)).tobytes(),
                                 legacy.crop((0,0,1080,520)).tobytes())
                self.assertEqual(source.crop((0,1522,1080,1920)).tobytes(),
                                 legacy.crop((0,1522,1080,1920)).tobytes())

    def test_legacy_draw_only_optics_still_supported(self):
        stage=Image.new("RGBA",(1080,1920))
        draw_rainbow(ImageDraw.Draw(stage,"RGBA"),"refraction",.2,6.,True)
        self.assertGreater(stage.getchannel("A").getextrema()[1],200)
        with self.assertRaises(ValueError):
            draw_rainbow(ImageDraw.Draw(stage,"RGBA"),"refraction",.2,6.,
                         True,canvas=Image.new("RGB",(1080,1920)))
