import {makeProject} from '@canvas-commons/core';
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/inter/800.css';
import '@fontsource/inter/900.css';
import '@fontsource/jetbrains-mono/500.css';
import '@fontsource/jetbrains-mono/700.css';

import s01 from './vinixedz/scenes/s01_hook?scene';
import s02 from './vinixedz/scenes/s02_title?scene';
import s03 from './vinixedz/scenes/s03_rules?scene';
import s04 from './vinixedz/scenes/s04_history?scene';
import s05 from './vinixedz/scenes/s05_vertical?scene';
import s06 from './vinixedz/scenes/s06_grammar?scene';
import s07 from './vinixedz/scenes/s07_stage?scene';
import s08 from './vinixedz/scenes/s08_creators?scene';
import s09 from './vinixedz/scenes/s09_anatomy?scene';
import s10 from './vinixedz/scenes/s10_compare?scene';
import s11 from './vinixedz/scenes/s11_numbers?scene';
import s12 from './vinixedz/scenes/s12_why?scene';
import s13 from './vinixedz/scenes/s13_ceiling?scene';
import s14 from './vinixedz/scenes/s14_future?scene';
import s15 from './vinixedz/scenes/s15_end?scene';

export default makeProject({
  name: 'vinixedz-the-standard-moved',
  scenes: [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13, s14, s15],
});
