import Recording from "../recording/Recording";
import styles from "./home.module.css";

export default function HomePage() {
  return (
    <>
      <div className={styles.title}>iCough</div>
      <Recording></Recording>
    </>
  );
}
