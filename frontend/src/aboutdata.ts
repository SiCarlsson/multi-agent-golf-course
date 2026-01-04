import emma from "./img/emma.png";
import simon from "./img/simon.png";

export const aboutData: Person[] = [
  {
    id: 1,
    name: "Simon Carlsson",
    imgSource: simon,
    git: "https://github.com/SiCarlsson",
    linkedIn: "https://www.linkedin.com/in/simonalexcarlsson/",
  },
  {
    id: 4,
    name: "Emma Lindblom",
    imgSource: emma,
    git: "https://github.com/emmalindblm",
    linkedIn: "www.linkedin.com/in/emma-lindblom-1b2ab01b4",
  },
];

export type Person = {
  id: number;
  name: string;
  imgSource: string;
  git: string;
  linkedIn?: string;
};
